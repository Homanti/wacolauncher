var skin = document.getElementById("input_skin");

document.getElementById("ram_range").addEventListener("input", function() {
    document.getElementById("ram_input").value = this.value;
});

document.getElementById("ram_input").addEventListener("blur", function() {
    const min = parseInt(this.min);
    const max = parseInt(this.max);
    let value = parseInt(this.value);

    if (value < min) {
        value = min;
    } else if (value > max) {
        value = max;
    }

    this.value = value;
    document.getElementById("ram_range").value = value;
});

document.getElementById("type-change-skin").addEventListener("input", function() {
    if (this.value == 1) {
        document.getElementById("input-id-document-plastic-surgery").style.display = "block";
    } else {
        document.getElementById("input-id-document-plastic-surgery").style.display = "none";
    }
});

async function get_accounts() {
    return await window.pywebview.api.get_accounts();
}

window.addEventListener('pywebviewready', async function() {
    const max_ram = await window.pywebview.api.get_max_ram();
    const data = await window.pywebview.api.readJson("data/settings.json");
    const ram = data["ram"];

    document.getElementById("ram_input").max = max_ram;
    document.getElementById("ram_range").max = max_ram;

    document.getElementById("ram_input").value = ram;
    document.getElementById("ram_range").value = ram;
});

document.getElementById("button_upload_skin").addEventListener("click", async function() {
    try {
        const active_account = window.pywebview.api.get_active_account();
        if (active_account.status_code === 200) {
            const skinFile = skin.files[0];

            const result = await window.pywebview.api.start_upload_skin(
                active_account.result[1],
                active_account.result[2],
                skinFile
            );

            if (result === true) {
                show_info_modal("Успешно", "Скин успешно изменен")
            }
            else if (result === 401) {
                open_tab("login.html");
            } else {
                show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
            }
        }
    } catch (error) {
        show_info_modal("Ошибка", "Произошла ошибка при смене скина. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
});

document.getElementById("button_update_password").addEventListener("click", async function() {
    const old_password = document.getElementById("input_old_password").value;
    const new_password = document.getElementById("input_new_password").value;

    const active_account = await window.pywebview.api.get_active_account();
    const result = await window.pywebview.api.update_password(active_account.result[1], old_password, new_password);

    if (result.status_code === 200) {
        show_info_modal("Успешно", "Пароль успешно изменен")
    } else if (result.status_code === 401) {
        show_info_modal("Ошибка", "Неверный пароль")
    } else {
        show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
    }
})

document.getElementById("button_delete_account").addEventListener("click", async function() {
    const password = document.getElementById("input_password").value;
    const active_account = await window.pywebview.api.get_active_account();

    const result = await window.pywebview.api.delete_account(active_account.result[1], password);

    if (result.status_code === 200) {
        show_info_modal("Успешно", "Аккаунт успешно удален")
    } else if (result.status_code === 401) {
        show_info_modal("Ошибка", "Неверный пароль")
    } else {
        show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
    }
})

document.getElementById("ram_range").addEventListener("input", async function() {
    let settings_json = await window.pywebview.api.readJson("data/settings.json");
    if (settings_json === null) {
        settings_json = {};
    }

    settings_json["ram"] = document.getElementById("ram_range").value;
    await window.pywebview.api.writeJson("data/settings.json", settings_json);
});

document.getElementById("ram_input").addEventListener("blur", async function() {
    let settings_json = await window.pywebview.api.readJson("data/settings.json");
    if (settings_json === null) {
        settings_json = {};
    }

    settings_json["ram"] = document.getElementById("ram_input").value;
    await window.pywebview.api.writeJson("data/settings.json", settings_json);
});