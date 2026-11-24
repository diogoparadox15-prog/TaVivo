#include <jni.h>
#include <string>
#include <vector>
#include <mutex>
#include <algorithm>
#include <android/log.h>

#ifdef HAVE_LLAMA_CPP
#include "llama.h"
#endif

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "TaVivoJNI", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "TaVivoJNI", __VA_ARGS__)

namespace {
std::mutex g_mutex;
#ifdef HAVE_LLAMA_CPP
llama_model* g_model = nullptr;
llama_context* g_ctx = nullptr;
constexpr int kMaxBatch = 512;
constexpr int kMaxCtx = 1536;

// Retorna quantos bytes iniciais de 's' formam sequencias UTF-8 completas
size_t valid_utf8_prefix_len(const std::string& s) {
    size_t i = 0;
    const size_t n = s.size();
    while (i < n) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        size_t need = 0;
        if ((c & 0x80) == 0) need = 1;
        else if ((c & 0xE0) == 0xC0) need = 2;
        else if ((c & 0xF0) == 0xE0) need = 3;
        else if ((c & 0xF8) == 0xF0) need = 4;
        else { i += 1; continue; } // byte invalido isolado: pula
        if (i + need > n) break; // caractere incompleto no final, aguarda proximo token
        i += need;
    }
    return i;
}
#endif
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_tavivo_app_LlamaBridge_nativeLoadModel(JNIEnv* env, jobject, jstring jpath, jint nThreads) {
    std::lock_guard<std::mutex> lock(g_mutex);
#ifdef HAVE_LLAMA_CPP
    const char* path = env->GetStringUTFChars(jpath, nullptr);
    llama_backend_init();

    if (g_ctx) { llama_free(g_ctx); g_ctx = nullptr; }
    if (g_model) { llama_model_free(g_model); g_model = nullptr; }

    llama_model_params mparams = llama_model_default_params();
    g_model = llama_model_load_from_file(path, mparams);
    env->ReleaseStringUTFChars(jpath, path);

    if (!g_model) {
        LOGE("Falha ao carregar modelo GGUF");
        return JNI_FALSE;
    }

    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx = kMaxCtx;
    cparams.n_batch = kMaxBatch;
    cparams.n_threads = nThreads > 0 ? nThreads : 4;
    cparams.n_threads_batch = cparams.n_threads + 2;
    g_ctx = llama_init_from_model(g_model, cparams);
    if (!g_ctx) {
        LOGE("Falha ao criar contexto llama");
        llama_model_free(g_model);
        g_model = nullptr;
        return JNI_FALSE;
    }
    LOGI("Modelo GGUF carregado com sucesso (threads=%d, batch=%d)", cparams.n_threads, kMaxBatch);
    return JNI_TRUE;
#else
    (void)env; (void)jpath; (void)nThreads;
    return JNI_FALSE;
#endif
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_tavivo_app_LlamaBridge_nativeIsLoaded(JNIEnv*, jobject) {
#ifdef HAVE_LLAMA_CPP
    return (g_model != nullptr && g_ctx != nullptr) ? JNI_TRUE : JNI_FALSE;
#else
    return JNI_FALSE;
#endif
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_tavivo_app_LlamaBridge_nativeGenerateStream(
    JNIEnv* env,
    jobject,
    jbyteArray jpromptBytes,
    jint maxTokens,
    jobject callback
) {
    std::lock_guard<std::mutex> lock(g_mutex);
#ifdef HAVE_LLAMA_CPP
    if (!g_model || !g_ctx || jpromptBytes == nullptr) {
        return JNI_FALSE;
    }
    jsize promptLen = env->GetArrayLength(jpromptBytes);
    std::string prompt(static_cast<size_t>(promptLen), '\0');
    if (promptLen > 0) {
        env->GetByteArrayRegion(jpromptBytes, 0, promptLen, reinterpret_cast<jbyte*>(&prompt[0]));
    }

    jmethodID onBytesMethod = nullptr;
    if (callback != nullptr) {
        jclass cbClass = env->GetObjectClass(callback);
        onBytesMethod = env->GetMethodID(cbClass, "onTokenBytes", "([B)V");
        env->DeleteLocalRef(cbClass);
    }

    auto emitBytes = [&](const std::string& chunk) -> bool {
        if (chunk.empty() || callback == nullptr || onBytesMethod == nullptr) return true;
        jbyteArray arr = env->NewByteArray(static_cast<jsize>(chunk.size()));
        if (!arr) return false;
        env->SetByteArrayRegion(arr, 0, static_cast<jsize>(chunk.size()), reinterpret_cast<const jbyte*>(chunk.data()));
        env->CallVoidMethod(callback, onBytesMethod, arr);
        env->DeleteLocalRef(arr);
        if (env->ExceptionCheck()) {
            env->ExceptionClear();
            return false;
        }
        return true;
    };

    const llama_vocab* vocab = llama_model_get_vocab(g_model);
    std::vector<llama_token> tokens(prompt.size() + 32);
    int nTokens = llama_tokenize(vocab, prompt.c_str(), static_cast<int>(prompt.size()), tokens.data(), static_cast<int>(tokens.size()), true, true);
    if (nTokens < 0) {
        tokens.resize(static_cast<size_t>(-nTokens));
        nTokens = llama_tokenize(vocab, prompt.c_str(), static_cast<int>(prompt.size()), tokens.data(), static_cast<int>(tokens.size()), true, true);
    }
    if (nTokens <= 0) {
        return JNI_FALSE;
    }
    if (nTokens > kMaxCtx - 300) {
        nTokens = kMaxCtx - 300;
    }
    tokens.resize(static_cast<size_t>(nTokens));

    llama_memory_clear(llama_get_memory(g_ctx), true);

    // Decodifica o prompt em blocos <= kMaxBatch para nunca disparar GGML_ASSERT
    for (int offset = 0; offset < nTokens; offset += kMaxBatch) {
        int chunkSize = std::min(kMaxBatch, nTokens - offset);
        llama_batch batch = llama_batch_get_one(tokens.data() + offset, chunkSize);
        if (llama_decode(g_ctx, batch) != 0) {
            LOGE("llama_decode falhou no prompt (offset=%d, size=%d)", offset, chunkSize);
            return JNI_FALSE;
        }
    }

    auto sparams = llama_sampler_chain_default_params();
    llama_sampler* sampler = llama_sampler_chain_init(sparams);
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.2f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(42));

    std::string utf8Pending;
    int limit = maxTokens > 0 ? maxTokens : 260;
    bool generatedAny = false;

    for (int i = 0; i < limit; ++i) {
        llama_token tok = llama_sampler_sample(sampler, g_ctx, -1);
        if (llama_vocab_is_eog(vocab, tok)) break;

        char buf[256];
        int n = llama_token_to_piece(vocab, tok, buf, sizeof(buf), 0, true);
        if (n > 0) {
            std::string piece(buf, static_cast<size_t>(n));
            if (piece.find("<|im_end|>") != std::string::npos || piece.find("<|endoftext|>") != std::string::npos) {
                break;
            }
            utf8Pending.append(piece);
            size_t ready = valid_utf8_prefix_len(utf8Pending);
            if (ready > 0) {
                std::string toSend = utf8Pending.substr(0, ready);
                utf8Pending.erase(0, ready);
                generatedAny = true;
                if (!emitBytes(toSend)) break;
            }
        }
        llama_batch next = llama_batch_get_one(&tok, 1);
        if (llama_decode(g_ctx, next) != 0) break;
    }

    if (!utf8Pending.empty()) {
        emitBytes(utf8Pending);
    }

    llama_sampler_free(sampler);
    return generatedAny ? JNI_TRUE : JNI_FALSE;
#else
    (void)jpromptBytes; (void)maxTokens; (void)callback;
    return JNI_FALSE;
#endif
}
