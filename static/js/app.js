document.addEventListener("DOMContentLoaded", function () {
    console.log("School Work ERP initialized");

    fetch("/health")
        .then(response => response.json())
        .then(data => {
            console.log("ERP Status:", data.status);
        })
        .catch(error => {
            console.error("Application Error:", error);
        });
});
