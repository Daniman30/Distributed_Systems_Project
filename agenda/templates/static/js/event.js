import {closeMenu} from './calendar.js';
import {manipulate} from './calendar.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');

// Crear evento
document.getElementById('btn_create_event').addEventListener('click', function () {
    // Obtener los valores de los inputs
    const eventName = document.getElementById('EventName').value;
    const eventDateInit = document.getElementById('EventDateInit').value;
    const eventTimeInit = document.getElementById('EventTimeInit').value; // Verificar si está marcado el checkbox
    const eventDateEnd = document.getElementById('EventDateEnd').value;
    const eventTimeEnd = document.getElementById('EventTimeEnd').value; // Verificar si está marcado el checkbox

    // Crear el objeto con los datos
    const data = {
        title: eventName,
        start_time: `${eventDateInit}T${eventTimeInit}`,
        end_time: `${eventDateEnd}T${eventTimeEnd}`
    };

    // Enviar los datos al endpoint
    fetch('http://127.0.0.1:8000/api/events/create/', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
        },
        body: JSON.stringify(data),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en el registro');
            }
            return response.json();
        })
        .then(data => {
            closeMenu();
            manipulate()
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Hubo un error al iniciar sesion');
        });
});

// Listar eventos
export function dailyEvents(day) {
    // Realizar la solicitud GET al endpoint de eventos
    return fetch('http://127.0.0.1:8000/api/events/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
        },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener eventos: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const date_day = new Date(day).toLocaleDateString()
            const personalEvents = data.personal_events.filter(event => 
                date_day >= new Date(event.start_time).toLocaleDateString() && date_day <= new Date(event.end_time).toLocaleDateString()
            );

            const groupEvents = data.group_events.filter(event => 
                date_day >= new Date(event.start_time).toLocaleDateString() && date_day <= new Date(event.end_time).toLocaleDateString()
            );
            return { personalEvents, groupEvents };
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al obtener los eventos');
        });
};
