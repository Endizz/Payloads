#include <node.h>
#include <curl/curl.h>
#include <fstream>
#include <string>

namespace addon {

size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    std::ofstream* file = static_cast<std::ofstream*>(userp);
    size_t totalSize = size * nmemb;
    file->write(static_cast<char*>(contents), totalSize);
    return totalSize;
}

void DownloadFile(const v8::FunctionCallbackInfo<v8::Value>& args) {
    v8::Isolate* isolate = args.GetIsolate();

    if (args.Length() < 2) {
        isolate->ThrowException(v8::Exception::TypeError(
            v8::String::NewFromUtf8(isolate, "Expected URL and output file path").ToLocalChecked()));
        return;
    }

    v8::String::Utf8Value url(isolate, args[0]);
    v8::String::Utf8Value output(isolate, args[1]);

    CURL* curl;
    CURLcode res;
    curl = curl_easy_init();
    if (!curl) {
        isolate->ThrowException(v8::Exception::Error(
            v8::String::NewFromUtf8(isolate, "Failed to initialize CURL").ToLocalChecked()));
        return;
    }

    std::ofstream file(*output, std::ios::binary);
    if (!file.is_open()) {
        isolate->ThrowException(v8::Exception::Error(
            v8::String::NewFromUtf8(isolate, "Failed to open output file").ToLocalChecked()));
        return;
    }

    curl_easy_setopt(curl, CURLOPT_URL, *url);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &file);

    res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    file.close();

    if (res != CURLE_OK) {
        isolate->ThrowException(v8::Exception::Error(
            v8::String::NewFromUtf8(isolate, "Download failed").ToLocalChecked()));
        return;
    }

    args.GetReturnValue().Set(v8::String::NewFromUtf8(isolate, "Download succeeded").ToLocalChecked());
}

void Initialize(v8::Local<v8::Object> exports) {
    NODE_SET_METHOD(exports, "downloadFile", DownloadFile);
}

NODE_MODULE(addon, Initialize)

}  // namespace addon