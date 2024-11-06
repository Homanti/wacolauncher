window.addEventListener('pywebviewready', function() {
    get_account_id();
});

async function check_discord_link() {
    const result = await window.pywebview.api.get_active_account();

    if (result.status_code === 200) {
        if (result.result[3]) {
            open_tab("index.html")
        }
    } else {
        if (result.status_code === 401) {
            open_tab("login.html")
        } else {
            show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
        }
    }
}

async function get_account_id() {
    const account = await window.pywebview.api.get_active_account();

    if (account.status_code === 200) {
        const discordLinkElement = document.getElementById("discord_link");
        discordLinkElement.innerHTML = `Для продолжения регистрации напишите "/link ${account.result[0]}" <a href="https://discord.gg/kEKgkx7Me7">в этом Discord канале</a>. После нажмите на кнопку.`;
    } else {
        show_info_modal("Ошибка", "Неверный логин или пароль")
    }
}
