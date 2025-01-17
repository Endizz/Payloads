{
  "targets": [
    {
      "target_name": "addon",
      "sources": ["addon.cc"],
      "include_dirs": [
        "C:/vcpkg/installed/x64-windows-static/include"
      ],
      "libraries": [
        "C:/vcpkg/installed/x64-windows-static/lib/libcurl.lib",
        "C:/vcpkg/installed/x64-windows-static/lib/zlib.lib",
        "-lws2_32",
        "-lwinmm",
        "-lcrypt32",
        "-lnormaliz",
        "-ladvapi32",
        "-luser32",
        "-lwldap32"
      ],
      "msvs_settings": {
        "VCCLCompilerTool": {
          "AdditionalOptions": ["/EHsc", "/MT"]
        }
      },
      "defines": [
        "CURL_STATICLIB"
      ]
    }
  ]
}
