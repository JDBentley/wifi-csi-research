#include <stdio.h>

#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_log.h"

static const char *TAG = "CSI_CAPTURE";

void csi_callback(void *ctx, wifi_csi_info_t *data) {
    printf("CSI len: %d\n", data->len);
}

void wifi_init(void) {
    esp_netif_init();
    esp_event_loop_create_default();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);

    esp_wifi_set_mode(WIFI_MODE_STA);

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = "Verizon-R562L5-071F",
            .password = "7176ff66",
        },
    };

    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_connect();

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