const nickname = document.getElementById('input_register_nickname');
const password = document.getElementById('input_register_password');
const history = document.getElementById('input_register_history');
const how_did_you_find = document.getElementById('input_register_how_did_you_find');
const skin = document.getElementById('input_register_skin');
const rulesCheckbox = document.getElementById('checkbox_register_rules');
const registerButton = document.getElementById('btn_register');

document.addEventListener('DOMContentLoaded', function () {
    function validateForm() {
        const fields = [nickname, password, history, how_did_you_find];
        const isFormValid = fields.every(field => field.value.trim() !== '') &&
                            skin.files.length > 0 &&
                            rulesCheckbox.checked;

        registerButton.disabled = !isFormValid;
    }

    // Привязываем событие 'input' ко всем полям для проверки формы в реальном времени
    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);
    history.addEventListener('input', validateForm);
    how_did_you_find.addEventListener('input', validateForm);
    skin.addEventListener('input', validateForm);
    rulesCheckbox.addEventListener('change', validateForm);

    // Начальная проверка формы
    validateForm();
});

async function register_account() {
    try {
        const file = skin.files[0];
        const fileReader = new FileReader();

        fileReader.onload = async function(event) {
            const fileBytes = new Uint8Array(event.target.result);
            const result = await window.pywebview.api.account_register(
                nickname.value,
                password.value,
                history.value,
                how_did_you_find.value,
                fileBytes
            );

            if (Array.isArray(result)) {
                if (result[3]) {from typing import Optional
                    from fastapi import FastAPI, HTTPException, File, UploadFile
                    from pydantic import BaseModel
                    import requests
                        from edit_db import *

                    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

                    GITHUB_TOKEN = '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'
                    REPO_OWNER = 'Homanti'
                    REPO_NAME = 'wacoskins'
                    BRANCH = 'main'


                    class RequestData(BaseModel):
                    action: str
                    nickname: str
                    password: str
                    rp_history: Optional[str] = None
                    how_did_you_find: Optional[str] = None


                @app.post("/database/")
                async def database(data: RequestData, skin_file: Optional[UploadFile] = File(None)):
                    if data.action not in ["login", "register", "delete", "upload_skin"]:
                    raise HTTPException(status_code=400, detail="Invalid type value")

                    if data.action == "login":
                    result = login_account(data.nickname, data.password)
                    if result:
                    return {"result": result, "detail": "Successful login to your account"}
                else:
                    raise HTTPException(status_code=401, detail="Invalid username or password")

                    elif data.action == "register":
                    result = register_account(data.nickname, data.password, data.rp_history, data.how_did_you_find)
                    if result:
                    return {"result": result, "detail": "Account successfully created"}
                else:
                    raise HTTPException(status_code=401, detail="Invalid username or password")

                    elif data.action == "delete":
                    result = delete_account(data.nickname, data.password)
                    if result:
                    raise HTTPException(status_code=200, detail="Account successfully deleted")
                else:
                    raise HTTPException(status_code=401, detail="Invalid username or password")

                    elif data.action == "upload_skin":
                    if skin_file is None:
                        raise HTTPException(status_code=400, detail="Skin file is required for upload.")

                    content = await skin_file.read()

                    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{data.nickname}.png'
                    headers = {
                        'Authorization': f'token {GITHUB_TOKEN}',
                        'Content-Type': 'application/json',
                    }

                    data_json = {
                        'content': content.decode('utf-8'),
                        'branch': BRANCH,
                    }

                    response = requests.put(url, headers=headers, json=data_json)

                    if response.status_code == 201:
                    return {"detail": f'Skin file successfully uploaded to repository {REPO_NAME}.'}

                else:
                    raise HTTPException(status_code=502, detail=f'Error uploading skin file: {response.json()}')

                else:
                    raise HTTPException(status_code=400, detail="Unsupported action")
                    open_tab("index.html");
                } else {
                    open_tab("link_discord_register.html");
                }
            } else {
                if (result === 401) {
                    showErrorModal("Неверный логин или пароль.");
                } else {
                    showErrorModal("Произошла непредвиденная ошибка. Попробуйте еще раз.");
                }
            }
        };

        fileReader.readAsArrayBuffer(file);

    } catch (error) {
        showErrorModal("Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
}

registerButton.addEventListener("click", function () {
    register_account();
});

document.addEventListener('click', function (event) {
    if (event.target.tagName === 'A' && event.target.href) {
        event.preventDefault();
        window.pywebview.api.open_link(event.target.href);
    }
});
