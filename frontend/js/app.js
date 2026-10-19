async function checkBackend() {

    const status =
        document.getElementById("status");


    try {

        const response =
            await fetch("/api/health");


        if (!response.ok) {

            throw new Error(
                `HTTP error: ${response.status}`
            );

        }


        const data =
            await response.json();


        if (data.success) {

            status.textContent =
                "Backend connected successfully ✅";

        } else {

            status.textContent =
                "Backend health check failed ❌";

        }


    } catch (error) {

        console.error(
            "Backend connection error:",
            error
        );


        status.textContent =
            "Could not connect to backend ❌";

    }

}


checkBackend();