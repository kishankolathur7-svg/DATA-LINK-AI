// ==================================================
// REGISTER
// ==================================================

const registerForm =
    document.getElementById("registerForm");


if (registerForm) {

    registerForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const name =
                document
                    .getElementById("name")
                    .value
                    .trim();


            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("password")
                    .value;


            const message =
                document.getElementById(
                    "registerMessage"
                );


            message.textContent =
                "Creating account...";


            try {

                const response =
                    await fetch(
                        "/api/auth/register",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                name,
                                email,
                                password
                            })
                        }
                    );


                const data =
                    await response.json();


                if (data.success) {

                    message.textContent =
                        "Registration successful! Redirecting...";


                    setTimeout(
                        function () {

                            window.location.href =
                                "/login.html";

                        },
                        1000
                    );


                } else {

                    message.textContent =
                        data.message;

                }


            } catch (error) {

                console.error(error);


                message.textContent =
                    "Unable to connect to backend.";

            }

        }
    );

}


// ==================================================
// LOGIN
// ==================================================

const loginForm =
    document.getElementById("loginForm");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const email =
                document
                    .getElementById("loginEmail")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("loginPassword")
                    .value;


            const message =
                document.getElementById(
                    "loginMessage"
                );


            message.textContent =
                "Logging in...";


            try {

                const response =
                    await fetch(
                        "/api/auth/login",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                email,
                                password
                            })
                        }
                    );


                const data =
                    await response.json();


                if (data.success) {

                    localStorage.setItem(
                        "productmind_user",
                        JSON.stringify(data.user)
                    );


                    message.textContent =
                        "Login successful!";


                    setTimeout(
                        function () {

                            window.location.href =
                                "/dashboard.html";

                        },
                        500
                    );


                } else {

                    message.textContent =
                        data.message;

                }


            } catch (error) {

                console.error(error);


                message.textContent =
                    "Unable to connect to backend.";

            }

        }
    );

}