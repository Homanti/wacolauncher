// Функция для обработки и изменения размера изображения (аналог Python-кода)
function processMinecraftSkin(imageSrc, canvas, width, height) {
    var image = new Image();
    image.src = imageSrc;

    image.onload = function() {
        // Определяем размеры головы (x, y, width, height)
        var headX = 8;
        var headY = 8;
        var headWidth = 8;
        var headHeight = 8;

        var context = canvas.getContext('2d');
        canvas.width = width;
        canvas.height = height;

        context.imageSmoothingEnabled = false; // Чтобы избежать размытия
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(image, headX, headY, headWidth, headHeight, 0, 0, width, height);
    };
}

// Функция для переключения дропдауна
function toggleDropdown() {
    update_dropdown();
    var dropdownMenu = document.getElementById("dropdownMenu");
    dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block";
}

// Функция для переключения аккаунтов
async function switchAccount(name, password) {
    const result = await window.pywebview.api.account_login(name, password);

    if (result.status_code === 401) {
        show_info_modal("Ошибка", "Неверный логин или пароль.");
        const accounts = await window.pywebview.api.readJson("data/credentials.json");

        if (accounts.length <= 0) {
            open_tab("login.html", "Ошибка", "Неверный логин или пароль.");
        } else {
            const active_account = await window.pywebview.api.get_active_account();
            switchAccount(active_account.nickname, active_account.password);
        }
    }

    document.getElementById("currentProfileName").textContent = name;

    var currentAvatarCanvas = document.getElementById("currentAvatarCanvas");
    processMinecraftSkin(`https://raw.githubusercontent.com/Homanti/wacoskins/main/${name}_skin.png`, currentAvatarCanvas, 50, 50);

    toggleDropdown();
}

window.addEventListener('pywebviewready', function() {
    update_dropdown();
});

// Функция для обновления дропдауна с аккаунтами
async function update_dropdown() {
    const accounts = await window.pywebview.api.readJson("data/credentials.json");
    updateDropdown(accounts);
}

// Функция для обновления содержимого дропдауна
function updateDropdown(accounts) {
    var dropdownMenu = document.getElementById("dropdownMenu");
    dropdownMenu.innerHTML = '';

    accounts.forEach(function(account) {
        var accountButton = document.createElement('button');
        accountButton.className = 'profile-button';
        accountButton.onclick = function() {
            switchAccount(account.nickname, account.password);
        };

        var avatarCanvas = document.createElement('canvas');
        avatarCanvas.width = 40;
        avatarCanvas.height = 40;
        avatarCanvas.className = 'profile-avatar';

        processMinecraftSkin(`https://raw.githubusercontent.com/Homanti/wacoskins/main/${account.nickname}_skin.png`, avatarCanvas, 40, 40);

        var profileDetails = document.createElement('div');
        profileDetails.className = 'profile-details';

        var profileName = document.createElement('div');
        profileName.className = 'profile-name';
        profileName.textContent = account.nickname;

        profileDetails.appendChild(profileName);
        accountButton.appendChild(avatarCanvas);
        accountButton.appendChild(profileDetails);

        if (account.active) {
            document.getElementById("currentProfileName").textContent = account.nickname;

            var currentAvatarCanvas = document.getElementById("currentAvatarCanvas");
            processMinecraftSkin(`https://raw.githubusercontent.com/Homanti/wacoskins/main/${account.nickname}_skin.png`, currentAvatarCanvas, 50, 50);
        }

        dropdownMenu.appendChild(accountButton);
    });

    var addButton = document.createElement('button');
    addButton.className = 'profile-button';
    addButton.onclick = function() {
        open_tab("login.html");
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

document.getElementById('btn_play').addEventListener('click', async function () {
    window.pywebview.api.start_minecraft();
});