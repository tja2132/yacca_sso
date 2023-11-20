import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
import json

from fastapi.staticfiles import StaticFiles

app = FastAPI()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
OAUTH_URL = os.environ["OAATH_URL"]

app.mount("/static", StaticFiles(directory="static"), name="static")

sso = GoogleSSO(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=OAUTH_URL + "/auth/callback",
    allow_insecure_http=True,
)


@app.get("/", response_class=HTMLResponse)
async def home_page():
    result = """
    <!DOCTYPE html>
    <html lang="en">
    <form action="{OAUTH_URL}/auth/login">
    <button type="submit" class="button">Login with Google</button>
    </form>
    </html>
    """
    result = result.replace("{OAUTH_URL}", OAUTH_URL)
    return result

@app.get("/auth/login")
async def auth_init():
    """Initialize auth and redirect"""
    with sso:
        return await sso.get_login_redirect(params={"prompt": "consent", "access_type": "offline"})


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    """Verify login"""
    print("Request = ", request)
    print("URL = ", request.url)

    try:
        with sso:
            user = await sso.verify_and_process(request)
            data = user

            html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>User Info</title>
                </head>
                <body>
                    <h1>User Information</h1>
                    <img src="{user.picture}" alt="User Picture" width="96" height="96"><br>
                    <p><b>ID:</b> {user.id}</p>
                    <p>Email: {user.email}</p>
                    <p>First Name: {user.first_name}</p>
                    <p>Last Name: {user.last_name}</p>
                    <p>Display Name: {user.display_name}</p>
                    <p>Identity Provider: {user.provider}</p>
                </body>
                </html>
                """

            return HTMLResponse(content=html_content)
    except Exception as e:
        print("Exception e = ", e)
        return RedirectResponse("/static/error.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
