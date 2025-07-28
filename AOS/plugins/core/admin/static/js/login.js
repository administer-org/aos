// pyxfluff 2025

const stayLoggedIn = new Switchery(document.querySelector('.js-switch'), { size: "small", secondaryColor: "#111417", "color": "#2548c2" });
const loginForm = document.getElementById('login');

loginForm.addEventListener('submit', e => {
    e.preventDefault();

    let data = {};
    (new FormData(loginForm)).forEach((value, key) => {
        data[key] = value;
    });

    data["stayLoggedIn"] = document.querySelector(".js-switch").checked

    console.log('Form data JSON:', JSON.stringify(data));
    document.querySelector("#login button").classList.add('shimmer');

    setTimeout(() => {
        document.querySelector("#login button").classList.remove('shimmer');
    }, 3000);
});
