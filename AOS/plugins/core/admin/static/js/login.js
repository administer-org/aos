// pyxfluff 2025

let stayLoggedIn;

try {
  stayLoggedIn = new Switchery(document.querySelector(".js-switch"), {
    size: "small",
    secondaryColor: "#111417",
    color: "#2548c2"
  });
} catch (e) {}

const loginForm = document.getElementById("login");
const signupForm = document.getElementById("signup");

if (loginForm != null) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();

    let data = {};
    new FormData(loginForm).forEach((value, key) => {
      data[key] = value;
    });

    data["stayLoggedIn"] = document.querySelector(".js-switch").checked;

    document.querySelector("#login button").classList.add("shimmer");

    // log in
    fetch("/admin/login", {
      method: "POST",
      body: JSON.stringify(data)
    })
      .then((reply) => reply.json())
      .then((respJSON) => {
        document.getElementById("login-feedback").innerText = respJSON["data"];
        document.getElementById("login-feedback").className =
          respJSON["code"] == 200 ? "good" : "bad";

        document.querySelector("#login button").classList.remove("shimmer");
      });
  });
} else {
  // Signup
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();

    let data = {};
    new FormData(loginForm).forEach((value, key) => {
      data[key] = value;
    });

    document.querySelector("#login button").classList.add("shimmer");

    fetch("/admin/signup", {
      method: "POST",
      body: JSON.stringify(data)
    })
      .then((reply) => reply.json())
      .then((respJSON) => {
        document.getElementById("login-feedback").innerText = respJSON["data"];
        document.getElementById("login-feedback").className =
          respJSON["code"] == 200 ? "good" : "bad";

        document.querySelector("#login button").classList.remove("shimmer");
      });
  });
}
