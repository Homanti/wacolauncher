window.addEventListener('pywebviewready', function() {
    get_id();
});

async function check_discord_link() {
    window.pywebview.api.check_discord_link();
}

async function get_id() {
    try {
        const idList = await window.pywebview.api.get_id(); // Получаем список ID
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
