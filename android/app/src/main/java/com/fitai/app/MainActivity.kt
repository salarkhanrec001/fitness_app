package com.fitai.app

import android.annotation.SuppressLint
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.CookieManager
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.fitai.app.BuildConfig.WEB_URL
import com.fitai.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    private val fileChooserLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val callback = fileChooserCallback ?: return@registerForActivityResult
            fileChooserCallback = null
            callback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data))
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupBackNavigation()
        setupWebView()

        if (savedInstanceState == null) {
            binding.webView.loadUrl(WEB_URL)
        } else {
            binding.webView.restoreState(savedInstanceState)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(binding.webView, true)

        binding.webView.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.allowContentAccess = true
            settings.allowFileAccess = true
            settings.loadsImagesAutomatically = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = true
            settings.builtInZoomControls = false
            settings.displayZoomControls = false

            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                    val uri = request?.url ?: return false
                    return if (uri.scheme == "http" || uri.scheme == "https") {
                        false
                    } else {
                        launchExternalUri(uri)
                    }
                }

                override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                    binding.progressBar.visibility = View.VISIBLE
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    binding.progressBar.visibility = View.GONE
                }

                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: android.webkit.WebResourceError?,
                ) {
                    if (request?.isForMainFrame == true) {
                        showOfflinePage()
                    }
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onProgressChanged(view: WebView?, newProgress: Int) {
                    binding.progressBar.progress = newProgress
                    binding.progressBar.visibility = if (newProgress >= 100) View.GONE else View.VISIBLE
                }

                override fun onShowFileChooser(
                    webView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams,
                ): Boolean {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = filePathCallback

                    return try {
                        fileChooserLauncher.launch(fileChooserParams.createIntent())
                        true
                    } catch (exception: Exception) {
                        Toast.makeText(
                            this@MainActivity,
                            "Unable to open file picker",
                            Toast.LENGTH_SHORT,
                        ).show()
                        fileChooserCallback = null
                        false
                    }
                }
            }
        }
    }

    private fun setupBackNavigation() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (binding.webView.canGoBack()) {
                    binding.webView.goBack()
                } else {
                    finish()
                }
            }
        })
    }

    private fun launchExternalUri(uri: Uri): Boolean {
        return try {
            val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, uri)
            startActivity(intent)
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun showOfflinePage() {
        binding.progressBar.visibility = View.GONE
        binding.webView.loadDataWithBaseURL(
            null,
            """
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <style>
                  :root { color-scheme: dark; }
                  body {
                    margin: 0;
                    font-family: sans-serif;
                    background: #0b1020;
                    color: #f4f7fb;
                    display: grid;
                    place-items: center;
                    min-height: 100vh;
                    padding: 24px;
                    box-sizing: border-box;
                    text-align: center;
                  }
                  .card {
                    max-width: 420px;
                    background: #121a32;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 20px;
                    padding: 28px;
                    box-shadow: 0 16px 48px rgba(0,0,0,0.35);
                  }
                  h1 { margin: 0 0 12px; font-size: 28px; }
                  p { margin: 0 0 20px; line-height: 1.6; color: #bac3d6; }
                  button {
                    appearance: none;
                    border: 0;
                    border-radius: 999px;
                    padding: 14px 22px;
                    background: #6c63ff;
                    color: white;
                    font-weight: 700;
                    font-size: 15px;
                  }
                </style>
              </head>
              <body>
                <div class="card">
                  <h1>FitAI is offline</h1>
                  <p>The Android app could not reach the web server. Make sure your Flask backend is running and the WEB_URL in the Android build points to an accessible address.</p>
                  <button onclick="window.location.reload()">Try again</button>
                </div>
              </body>
            </html>
            """.trimIndent(),
            "text/html",
            "UTF-8",
            null,
        )
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        binding.webView.saveState(outState)
    }

    override fun onDestroy() {
        fileChooserCallback?.onReceiveValue(null)
        fileChooserCallback = null
        binding.webView.destroy()
        super.onDestroy()
    }
}
