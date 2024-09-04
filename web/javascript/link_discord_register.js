window.addEventListener('pywebviewready', function() {
    get_account_id();
});

async function check_discord_link() {
    const result = await window.pywebview.api.check_discord_link();

    if (Array.isArray(result)) {
        if (result[3]) {
            open_tab("index.html")
        }
    } else {
        if (result === 401) {
            open_tab("login.html")
            show_info_modal("Ошибка", "Неверный логин или пароль.");
        } else {
            show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
        }
    }
}

async function get_account_id() {
    try {
        const idList = await window.pywebview.api.get_account_id(); // Получаем список ID
        if (idList && idList.length > 0) {
            const firstId = idList[0]; // Берем первый элемент списка
            const discordLinkElement = document.getElementById("discord_link");
            discordLinkElement.innerHTML = `Для продолжение регистрации напишите "/link ${firstId}" <a href="https://discord.gg/8YCNBakvpC">в этом Discord канале</a>. После нажмите на кнопку.`;
        } else {
            console.error("Список ID пуст или не был получен.");
        }
    } catch (error) {
        console.error("Ошибка при получении ID:", error);
    }
}
