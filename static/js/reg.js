function submitForm(event) {
    event.preventDefault();

    const errorMessagesDiv = document.getElementById('error-messages');
    const formFields = document.querySelectorAll('.form-control');
    formFields.forEach(field => field.classList.remove('is-invalid'));
    const errorContainers = document.querySelectorAll('.invalid-feedback');
    errorContainers.forEach(container => container.innerHTML = '');

    const formData = new FormData(document.getElementById('registration-form'));

    fetch('/register', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.errors && data.errors.length > 0) {
            data.errors.forEach(error => {
                const [field, message] = error.split(':');
                const fieldElement = document.getElementById(field);
                const errorContainer = document.getElementById(`${field}-error`);

                fieldElement.classList.add('is-invalid');
                errorContainer.innerHTML = message;
            });
        } else if (data.success) {
            window.location.href = '/';
        } else if (data.flash_message) {
            alert(data.flash_message);
        }
    })
    .catch(error => {
        console.error('Ошибка при регистрации:', error);
    });
}