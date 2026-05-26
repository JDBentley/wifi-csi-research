#include <stdio.h>
#include <inttypes.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

#include "wifi_config.h"

#define FIRMWARE_VERSION "0.2.0-csi-rxctrl"

static const char *TAG = "CSI_CAPTURE";

void csi_callback(void *ctx, wifi_csi_info_t *data) {
    int64_t timestamp = esp_timer_get_time();
    wifi_pkt_rx_ctrl_t *rc = &data->rx_ctrl;

    /* C6 + HE: esp_wifi_rxctrl_t layout.
     * No sig_mode/mcs/cwb/ant on this chip — they don't exist in the struct.
     * cur_bb_format is the discriminator we actually want (RX_BB_FORMAT_*).
     * noise_floor tests the AGC hypothesis directly.
     */
    printf("CSI,%lld,%d,%u,%d,%u,%u,%u,%u,%u,%u,%d",
        timestamp,                  // local esp_timer_get_time()
        rc->rssi,                   // dBm
        rc->rate,                   // 5-bit PHY rate / L-SIG rate
        rc->noise_floor,            // dBm
        rc->channel,                // primary channel
        rc->second,                 // secondary channel (HT40)
        rc->cur_bb_format,          // 11B/11G/HT/VHT/HE_SU/HE_MU/HE_ERSU/HE_TB/VHT_MU
        rc->sig_len,                // MPDU length incl FCS
        rc->rx_state,               // 0 = success
        rc->rxend_state,            // 0 = success
        data->len                   // CSI buffer length in bytes
    );

    for (int i = 0; i < data->len; i++) {
        printf(",%d", data->buf[i]);
    }

    printf("\n");
}

void print_ip_info(void) {
    esp_netif_ip_info_t ip_info;
    esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");

    if (netif == NULL) {
        printf("ESP IP: netif not ready\n");
        return;
    }

    esp_netif_get_ip_info(netif, &ip_info);

    printf("ESP IP: " IPSTR "\n", IP2STR(&ip_info.ip));
}

void wifi_init(void) {
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);

    esp_wifi_set_mode(WIFI_MODE_STA);

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASSWORD,
        },
    };

    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_set_ps(WIFI_PS_NONE);
    esp_wifi_connect();

    vTaskDelay(pdMS_TO_TICKS(5000));

    print_ip_info();

    /* HE SU re-enabled to restore packet rate.
    * v0.1.x had every flag on, mixing legacy/HT/HE/MU/DCM/beamformed/STBC
    * into one stream. v0.2.x narrows to legacy + HE SU only, and
    * cur_bb_format in rx_ctrl tells us which one each packet was.
    * If bimodality persists with two cur_bb_format values, we've found it.
    * If bimodality persists with a single cur_bb_format value, we have
    * to look at rate/MCS or AGC variation within that format.
    */
    wifi_csi_config_t csi_config = {
        .enable = true,
        .acquire_csi_legacy = true,
        .acquire_csi_ht20 = true,        // <-- back on; this is what your link uses
        .acquire_csi_ht40 = false,       // stay off; link is BW20
        .acquire_csi_su = false,         // stay off; he:0
        .acquire_csi_mu = false,
        .acquire_csi_dcm = false,
        .acquire_csi_beamformed = false,
        .acquire_csi_he_stbc = 0,
        .val_scale_cfg = 0,
        .dump_ack_en = false,
    };

    esp_wifi_set_csi_rx_cb(&csi_callback, NULL);
    esp_wifi_set_csi_config(&csi_config);
    esp_wifi_set_csi(true);
}

void app_main(void) {
    nvs_flash_init();
    ESP_LOGI(TAG, "CSI capture firmware %s", FIRMWARE_VERSION);
    wifi_init();
}