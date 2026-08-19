window.safeFetch = function(url, options) {
    return fetch(url, options).then(function(response) {
        if (!response.ok) {
            return response.text().then(function(text) {
                var msg = '请求失败 (HTTP ' + response.status + ')';
                try { var j = JSON.parse(text); if (j.message) msg = j.message; if (j.error) msg = j.error; } catch(e) {}
                throw new Error(msg);
            });
        }
        return response;
    }).catch(function(err) {
        if (err.message && err.message.indexOf('Failed to fetch') !== -1) {
            throw new Error('网络连接失败，请检查服务器是否正常运行');
        }
        throw err;
    });
};