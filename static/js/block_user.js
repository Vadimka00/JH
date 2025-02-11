document.querySelectorAll('.block-btn').forEach(button => {
    button.addEventListener('click', function() {
        const userLogin = this.getAttribute('data-account-id');

        fetch('/block_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_login: userLogin
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                location.reload();
            } else {
                alert('Произошла ошибка: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            location.reload();
        });
    });
});
