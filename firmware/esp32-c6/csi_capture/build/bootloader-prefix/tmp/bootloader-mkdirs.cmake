# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/cerd/esp/esp-idf/components/bootloader/subproject"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/tmp"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/src/bootloader-stamp"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/src"
  "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/cerd/Developer/wifi-csi-research/firmware/esp32-c6/csi_capture/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
