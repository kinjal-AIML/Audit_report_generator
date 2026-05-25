document.addEventListener("DOMContentLoaded", () => {
    const chk = document.getElementById("chk");
    document.querySelectorAll("label[for='chk']").forEach(label => {
        label.addEventListener("click", () => {
            setTimeout(() => {
                const active = chk.checked ? "Signup" : "Login";
                console.log(`${active} form opened`);
            }, 200);
        });
    });
});
