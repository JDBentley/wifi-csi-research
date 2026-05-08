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

static const char *TAG = "CSI_CAPTURE";

void csi_callback(void *ctx, wifi_csi_info_t *data) {
    int64_t timestamp = esp_timer_get_time();

    printf("CSI,%lld,%d,%d", timestamp, data->rx_ctrl.rssi, data->len);

    for (int i = 0; i < 16 && i < data->len; i++) {
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
            .ssid = "Verizon-R562L5-071F",
            .password = "7176ff66",
        },
    };

    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_set_ps(WIFI_PS_NONE);
    esp_wifi_connect();

    vTaskDelay(pdMS_TO_TICKS(5000));

    print_ip_info();

    wifi_csi_config_t csi_config = {
        .enable = true,
        .acquire_csi_legacy = true,
        .acquire_csi_ht20 = true,
        .acquire_csi_ht40 = true,
        .acquire_csi_su = true,
        .acquire_csi_mu = true,
        .acquire_csi_dcm = true,
        .acquire_csi_beamformed = true,
        .val_scale_cfg = 0,
        .dump_ack_en = false,
    };

    esp_wifi_set_csi_rx_cb(&csi_callback, NULL);
    esp_wifi_set_csi_config(&csi_config);
    esp_wifi_set_csi(true);
}

void app_main(void) {
    nvs_flash_init();
    wifi_init();
}