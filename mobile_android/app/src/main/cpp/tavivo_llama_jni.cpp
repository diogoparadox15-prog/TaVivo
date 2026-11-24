#include <jni.h>
#include <string>
#include <vector>
#include <mutex>
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
    cparams.n_ctx = 1536;
    cparams.n_batch = 256;
    // Em CPUs ARM64 big.LITTLE, 4 threads nos nucleos de performance evitam gargalo nos nucleos lentos
    cparams.n_threads = nThreads > 0 ? nThreads : 4;
    cparams.n_threads_batch = cparams.n_threads + 2;
    g_ctx = llama_init_from_model(g_model, cparams);
    if (!g_ctx) {
        LOGE("Falha ao criar contexto llama");
        llama_model_free(g_model);
        g_model = nullptr;
        return JNI_FALSE;
    }
    LOGI("Modelo GGUF carregado com sucesso (threads=%d)", cparams.n_threads);
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

extern "C" JNIEXPORT jstring JNICALL
Java_com_tavivo_app_LlamaBridge_nativeGenerateStream(
    JNIEnv* env,
    jobject,
    jstring jprompt,
    jint maxTokens,
    jobject callback
) {
    std::lock_guard<std::mutex> lock(g_mutex);
#ifdef HAVE_LLAMA_CPP
    if (!g_model || !g_ctx) {
        return env->NewStringUTF("");
    }
    const char* promptChars = env->GetStringUTFChars(jprompt, nullptr);
    std::string prompt(promptChars ? promptChars : "");
    env->ReleaseStringUTFChars(jprompt, promptChars);

    jmethodID onTokenMethod = nullptr;
    if (callback != nullptr) {
        jclass cbClass = env->GetObjectClass(callback);
        onTokenMethod = env->GetMethodID(cbClass, "onToken", "(Ljava/lang/String;)V");
        env->DeleteLocalRef(cbClass);
    }

    const llama_vocab* vocab = llama_model_get_vocab(g_model);
    std::vector<llama_token> tokens(prompt.size() + 32);
    int nTokens = llama_tokenize(vocab, prompt.c_str(), (int)prompt.size(), tokens.data(), (int)tokens.size(), true, true);
    if (nTokens < 0) {
        tokens.resize(-nTokens);
        nTokens = llama_tokenize(vocab, prompt.c_str(), (int)prompt.size(), tokens.data(), (int)tokens.size(), true, true);
    }
    if (nTokens > 1200) {
        nTokens = 1200;
    }
    tokens.resize(nTokens);

    llama_memory_clear(llama_get_memory(g_ctx), true);
    llama_batch batch = llama_batch_get_one(tokens.data(), (int)tokens.size());
    if (llama_decode(g_ctx, batch) != 0) {
        return env->NewStringUTF("Erro ao processar prompt no motor local.");
    }

    auto sparams = llama_sampler_chain_default_params();
    llama_sampler* sampler = llama_sampler_chain_init(sparams);
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.2f));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(42));

    std::string output;
    int limit = maxTokens > 0 ? maxTokens : 280;
    for (int i = 0; i < limit; ++i) {
        llama_token tok = llama_sampler_sample(sampler, g_ctx, -1);
        if (llama_vocab_is_eog(vocab, tok)) break;

        char buf[256];
        int n = llama_token_to_piece(vocab, tok, buf, sizeof(buf), 0, true);
        if (n > 0) {
            std::string piece(buf, n);
            if (piece.find("<|im_end|>") != std::string::npos || piece.find("<|endoftext|>") != std::string::npos) {
                break;
            }
            output.append(piece);
            if (callback != nullptr && onTokenMethod != nullptr) {
                jstring jpiece = env->NewStringUTF(piece.c_str());
                env->CallVoidMethod(callback, onTokenMethod, jpiece);
                env->DeleteLocalRef(jpiece);
            }
        }
        llama_batch next = llama_batch_get_one(&tok, 1);
        if (llama_decode(g_ctx, next) != 0) break;
    }

    llama_sampler_free(sampler);
    return env->NewStringUTF(output.c_str());
#else
    (void)jprompt; (void)maxTokens; (void)callback;
    return env->NewStringUTF("");
#endif
}
