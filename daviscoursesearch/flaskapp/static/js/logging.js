window.onerror = function(message, url, lineno, colno) {
    var formData = new FormData();
    formData.append('message', message);
    formData.append('url', window.location);
    formData.append('linecol', [url, lineno, colno].join(':'));
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/log_error');
    xhr.send(formData);
}