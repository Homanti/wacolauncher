// Функция для переключения отображения дропдауна
function toggleDropdown() {
    get_accounts()
    var dropdownMenu = document.getElementById("dropdownMenu");
    dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block";
}

// Функция для переключения аккаунтов
function switchAccount(name, password, avatar) {
    window.pywebview.api.account_login(name, password);
    document.getElementById("currentProfileName").textContent = name; // Изменяем имя профиля
    document.getElementById("currentAvatar").src = avatar; // Изменяем аватар
    toggleDropdown(); // Закрываем дропдаун после выбора
}

window.addEventListener('pywebviewready', function() {
    get_accounts();
});

async function get_accounts() {
    const accounts = await pywebview.api.get_accounts();
    updateDropdown(accounts);
}

// Функция для обновления дропдауна с аккаунтами
function updateDropdown(accounts) {
    var dropdownMenu = document.getElementById("dropdownMenu");
    dropdownMenu.innerHTML = ''; // Очищаем текущее содержимое

    accounts.forEach(function(account) {
        // Создаем элемент для каждого аккаунта
        var accountButton = document.createElement('button');
        accountButton.className = 'profile-button';
        accountButton.onclick = function() {
            switchAccount(account.nickname, account.password, 'https://placehold.co/50x50'); // Используйте актуальные URL для аватаров
        };

        // Создаем аватар и имя профиля
        var avatar = document.createElement('img');
        avatar.src = 'https://placehold.co/50x50'; // Используйте актуальные URL для аватаров
        avatar.alt = 'Avatar';
        avatar.className = 'profile-avatar';

        var profileDetails = document.createElement('div');
        profileDetails.className = 'profile-details';

        var profileName = document.createElement('div');
        profileName.className = 'profile-name';
        profileName.textContent = account.nickname;

        profileDetails.appendChild(profileName);
        accountButton.appendChild(avatar);
        accountButton.appendChild(profileDetails);

        // Если аккаунт активен, обновляем текущий профиль
        if (account.active) {
            document.getElementById("currentProfileName").textContent = account.nickname;
            document.getElementById("currentAvatar").src = 'https://placehold.co/50x50'; // Используйте актуальные URL для аватаров
        }

        dropdownMenu.appendChild(accountButton);
    });

    // Добавляем кнопку "Добавить аккаунт"
    var addButton = document.createElement('button');
    addButton.className = 'profile-button';
    addButton.onclick = function() {
        window.pywebview.api.load_tab("login.html")
    };

    var addProfileDetails = document.createElement('div');
    addProfileDetails.className = 'profile-details';

    var addProfileName = document.createElement('div');
    addProfileName.className = 'profile-name';
    addProfileName.textContent = 'Добавить аккаунт';

    addProfileDetails.appendChild(addProfileName);
    addButton.appendChild(addProfileDetails);

    dropdownMenu.appendChild(addButton);
}

// Закрываем дропдаун при клике вне его области
window.onclick = function(event) {
    if (!event.target.closest('.profile-dropdown')) {
        var dropdowns = document.getElementsByClassName("dropdown-menu");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.style.display === "block") {
                openDropdown.style.display = "none";
            }
        }
    }
}