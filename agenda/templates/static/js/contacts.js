import {closeMenu} from './calendar.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');

document.getElementById('btn_add_contact').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const username = document.getElementById('exampleInputUsername').value;
    const email = document.getElementById('exampleInputEmail').value;

    // Crear el objeto con los datos
    const data = {
        username: username,
        email: email,
    };

    // Enviar los datos al endpoint
    fetch('http://127.0.0.1:8000/api/get_user_id/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener el ID de usuario: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Redirigir al usuario
            const contactData = {
                contact: data.id
            };

            fetch('http://127.0.0.1:8000/api/contacts/', {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`,
                },
                body: JSON.stringify(contactData),
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(`Error al crear el contacto: ${err.detail || err}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // Redirigir al usuario
                    closeMenu()
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Hubo un error al crear el contacto');
                });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Hubo un error al obtener el ID de usuario');
        });
});

// List Contacts
document.getElementById('list_contacts').addEventListener('click', function () {
    // Realizar la solicitud GET al endpoint de contactos
    fetch('http://127.0.0.1:8000/api/contacts/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                // Manejar errores si la respuesta no es exitosa
                return response.json().then(err => {
                    throw new Error(`Error al obtener contactos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Mostrar los contactos en la consola o en la UI
            console.log('Contactos obtenidos:', data);

            // Aquí puedes manipular los datos para mostrarlos en la página
            const contactList = document.getElementById('contact-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            contactList.innerHTML = ''; // Limpiar cualquier contenido previo

            data.forEach(contact => {
                const listItem = document.createElement('li');
                listItem.textContent = `${contact.contact_name}`;

                // Crear el ícono de basura
                const trashIcon = document.createElement('i');
                trashIcon.className = 'fas fa-trash-alt';
                trashIcon.style.paddingLeft = '5px'; // Espacio entre el nombre y el ícono

                // Agregar el ícono al elemento de lista
                listItem.appendChild(trashIcon);

                // Agregar el elemento de lista al contenedor
                contactList.appendChild(listItem);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al obtener los contactos');
        });
});