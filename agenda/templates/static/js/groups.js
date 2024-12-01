import {closeMenu} from './calendar.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');

document.getElementById('btn_create_group').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const GroupName = document.getElementById('GroupName').value;
    const GroupDescription = document.getElementById('GroupDescription').value;
    const is_hierarchical = document.getElementById('is_hierarchical').checked; // Verificar si está marcado el checkbox
    var data = 0
    
    if(is_hierarchical) {
        data = {
            name: GroupName,
            description: GroupDescription,
            is_hierarchical: true
        };
    } else {
        data = {
            name: GroupName,
            description: GroupDescription,
            is_hierarchical: false
        };
    }
    // Crear el objeto con los datos
    

    // Enviar los datos al endpoint
    fetch('http://127.0.0.1:8000/api/groups/', {
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
                    throw new Error(`Error al crear el grupo: ${err.detail || err}`);
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
            alert('Hubo un error al crear el grupo');
        });
});

// List Contacts
document.getElementById('list_groups').addEventListener('click', function () {
    // Realizar la solicitud GET al endpoint de contactos
    fetch('http://127.0.0.1:8000/api/groups/', {
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
                    throw new Error(`Error al obtener grupos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Mostrar los contactos en la consola o en la UI
            console.log('Grupos obtenidos:', data);

            // Aquí puedes manipular los datos para mostrarlos en la página
            const groupList = document.getElementById('group-list'); // Asegúrate de tener un contenedor en tu HTML con este ID
            groupList.innerHTML = ''; // Limpiar cualquier contenido previo

            data.forEach(group => {
                const Item = document.createElement('li');

                const nameItem = document.createElement('h5');
                nameItem.textContent = `${group.name}`;
                
                // Descripcion del grupo
                const description = document.createElement('p');
                description.textContent = `${group.description}`;

                // Tiene jerarquia?
                const hierarchical = document.createElement('p');
                hierarchical.textContent = ' is hierachical'

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox'; // Define el tipo como checkbox
                checkbox.checked = group.is_hierarchical; // Marcar/desmarcar según el valor de group.is_hierarchical
                checkbox.disabled = true; // Hacer que no se pueda cambiar su estado

                hierarchical.appendChild(checkbox);
                
                // Crear el ícono de basura
                const trashIcon = document.createElement('i');
                trashIcon.className = 'fas fa-trash-alt';
                trashIcon.style.paddingLeft = '5px'; // Espacio entre el nombre y el ícono
                
                // Crear divider
                const divider = document.createElement('hr')
                divider.className = 'sidebar-divider'

                // Agregar elementos a la lista
                Item.appendChild(nameItem)
                nameItem.appendChild(trashIcon);
                Item.appendChild(description);
                Item.appendChild(hierarchical);

                // Agregar el elemento de lista al contenedor
                groupList.appendChild(Item);
                groupList.appendChild(divider);
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Error al obtener grupos');
        });
});