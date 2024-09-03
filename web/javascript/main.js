function open_tab(html_name) {
    window.pywebview.api.load_tab(html_name)
}

function showErrorModal(errorMessage) {
    document.getElementById('errorModalText').innerText = errorMessage;
    var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    errorModal.show();
}