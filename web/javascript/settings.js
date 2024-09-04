var skin = document.getElementById("input_skin");

document.getElementById("ram-range").addEventListener("input", function() {
    document.getElementById("ram-input").value = this.value;
});

document.getElementById("ram-input").addEventListener("blur", function() {
    const min = parseInt(this.min);
    const max = parseInt(this.max);
    let value = parseInt(this.value);

    if (value < min) {
        value = min;
    } else if (value > max) {
        value = max;
    }

    this.value = value;
    document.getElementById("ram-range").value = value;
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

document.getElementById("button_upload_skin").addEventListener("click", async function() {
    try {
        const file = skin.files[0];
        const fileReader = new FileReader();
        const accounts = await get_accounts(); // Ожидаем асинхронный вызов

        let activeAccount = null;

        for (let i = 0; i < accounts.length; i++) {
            if (accounts[i]["active"]) { // Проверяем каждый элемент массива accounts
                activeAccount = accounts[i];
                break;
            }
        }

        fileReader.onload = async function(event) {
            const fileBytes = new Uint8Array(event.target.result);
            const result = await window.pywebview.api.start_upload_skin(
                activeAccount["nickname"],
                activeAccount["password"],
                fileBytes
            );

            if (result === true) {
                show_info_modal("Успешно", "Скин успешно изменен")
            }
            else if (result === 401) {
                open_tab("login.html");
            } else {
                show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
            }
        };

        fileReader.readAsArrayBuffer(file);

    } catch (error) {
        show_info_modal("Ошибка", "Произошла ошибка при смене скина. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
});

document.getElementById("button_update_password").addEventListener("click", async function() {
    const accounts = await get_accounts();
    const old_password = document.getElementById("input_old_password").value;
    const new_password = document.getElementById("input_new_password").value;

    let activeAccount = null;

    for (let i = 0; i < accounts.length; i++) {
        if (accounts[i]["active"]) {
            activeAccount = accounts[i];
            break;
        }
    }

    const result = await window.pywebview.api.update_password(activeAccount["nickname"], old_password, new_password);

    if (result === 200) {
        show_info_modal("Успешно", "Пароль успешно изменен")
    } else if (result === 401) {
        show_info_modal("Ошибка", "Неверный пароль")
    } else {
        show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
    }
})

document.getElementById("button_delete_account").addEventListener("click", async function() {
    const accounts = await get_accounts();
    const password = document.getElementById("input_password").value;

    let activeAccount = null;

    for (let i = 0; i < accounts.length; i++) {
        if (accounts[i]["active"]) {
            activeAccount = accounts[i];
            break;
        }
    }

    const result = await window.pywebview.api.delete_account(activeAccount["nickname"], password);

    if (result === 200) {
        show_info_modal("Успешно", "Аккаунт успешно удален")
    } else if (result === 401) {
        show_info_modal("Ошибка", "Неверный пароль")
    } else {
        show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
    }
})