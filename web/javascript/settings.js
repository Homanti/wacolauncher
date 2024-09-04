var skin = document.getElementById("input_skin")

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

document.getElementById("button_upload").addEventListener("click", function() {
    try {
        const file = skin.files[0];
        const fileReader = new FileReader();
        const result = get_accounts();
        let activeAccount = null;

        for (let i = 0; i < result.length; i++) {
            if (result[i].active) {
                activeAccount = result[i];
                break;
            }
        }

        fileReader.onload = async function(event) {
            const fileBytes = new Uint8Array(event.target.result);
            const result = await window.pywebview.api.upload_skin(
                activeAccount["nickname"],
                activeAccount["password"],
                fileBytes
            );

            if (Array.isArray(result)) {
                if (!result[3]) {
                    open_tab("link_discord_register.html");
                }
            } else {
                if (result === 401) {
                    showErrorModal("Неверный логин или пароль.");
                    open_tab("login.html");
                } else {
                    showErrorModal("Произошла непредвиденная ошибка. Попробуйте еще раз.");
                }
            }
        };

        fileReader.readAsArrayBuffer(file);

    } catch (error) {
        showErrorModal("Произошла ошибка при смене скина. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
});

