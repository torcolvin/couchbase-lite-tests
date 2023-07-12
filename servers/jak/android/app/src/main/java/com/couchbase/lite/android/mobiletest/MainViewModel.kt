//
// Copyright (c) 2023 Couchbase, Inc All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
package com.couchbase.lite.android.mobiletest

import androidx.lifecycle.ViewModel
import com.couchbase.lite.android.mobiletest.util.url
import com.couchbase.lite.mobiletest.Server
import com.couchbase.lite.mobiletest.util.Log
import java.io.IOException
import java.net.URI


private const val TAG = "MAIN"

class MainViewModel(private val server: Server) : ViewModel() {
    fun startServer(): URI? {
        try {
            server.start()
            val uri = server.url()
            Log.i(TAG, "Server launched at $uri")
            return uri
        } catch (e: IOException) {
            Log.e(TAG, "Failed starting server", e)
            throw e
        }
    }

    fun stopServer() {
        server.stop()
    }
}