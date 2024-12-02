import {closeMenu} from './calendar.js';
import {manipulate} from './calendar.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');

let activeMenu2 = null;
const overlay2 = document.getElementById('overlay2');

// Crear evento
document.getElementById('btn_create_event').addEventListener('click', async function () {
    // Obtener los valores de los inputs
    const eventName = document.getElementById('EventName').value;
    const eventDateInit = document.getElementById('EventDateInit').value;
    const eventTimeInit = document.getElementById('EventTimeInit').value;
    const eventDateEnd = document.getElementById('EventDateEnd').value;
    const eventTimeEnd = document.getElementById('EventTimeEnd').value;
    const eventDescription = document.getElementById('EventDescription').value;
    const eventPrivacyCheck = document.getElementById('checkPrivacy').checked;
    const eventPrivacy = eventPrivacyCheck ? 'private' : 'public';
    const groupEvent = document.getElementById('EventGroup').value;
    const participantsEvent = document.getElementById('EventParticipants').value;

    const numbers = participantsEvent 
    ? participantsEvent.split(',').map(num => parseFloat(num.trim())).filter(num => !isNaN(num)) 
    : [];

    const rawData = {
        title: eventName,
        start_time: `${eventDateInit}T${eventTimeInit}`,
        end_time: `${eventDateEnd}T${eventTimeEnd}`,
        description: eventDescription || null,
        privacy: eventPrivacy,
        group: groupEvent || null,
        participants: numbers.length > 0 ? numbers : null
    };

    const data = Object.fromEntries(Object.entries(rawData).filter(([_, value]) => value !== null));

    console.log(data)

    try {
        // Enviar los datos al endpoint
        const response = await fetch('http://127.0.0.1:8000/api/events/create/', {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`,
            },
            body: JSON.stringify(data),
            
        });

        if (!response.ok) {
            throw new Error('Error en el registro');
        }

        const result = await response.json();

        // Llama a manipulate y espera a que se complete
        await manipulate();
        closeMenu();
    } catch (error) {
        console.error('Error:', error);
        alert('Hubo un error al procesar la solicitud.');
    }
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

// View Event
function viewEvent(idEvent) {
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
            const EventFinal = data.personal_events.filter(event => 
                event.id === idEvent
            );
            if (EventFinal.length < 1) {
                return response.json().then(err => {
                    throw new Error(`Error al obtener eventos: ${err.detail || err}`);
                });
            } 
            return EventFinal[0];
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al obtener los eventos');
        });
}

document.getElementById('alertsDropdown').addEventListener('click', function () {
    return fetch('http://127.0.0.1:8000/api/events/pending/', {
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

            const menuEvent = document.getElementById('EventsPending')
            data.forEach(element => {
                const Aelement = document.createElement('a');
                Aelement.classList = ["dropdown-item d-flex align-items-center"];
                menuEvent.appendChild(Aelement)

                const divElement1 = document.createElement('div');
                divElement1.className = "mr-3"
                Aelement.appendChild(divElement1)

                const divElement2 = document.createElement('div');
                divElement2.classList = ["icon-circle bg-primary"]
                divElement1.appendChild(divElement2)

                const iElement = document.createElement('i');
                iElement.className = ["fas fa-file-alt text-white"]
                divElement2.appendChild(iElement)

                const divElement3 = document.createElement('div');
                Aelement.appendChild(divElement3)

                const divElement4 = document.createElement('div');
                divElement4.className = ["small text-gray-500"]
                divElement4.id = "DateInitEventPending"
                divElement4.textContent = formatToReadableDate(element.start_time)
                divElement3.appendChild(divElement4)

                const spanElement = document.createElement('span');
                spanElement.className = "font-weight-bold"
                spanElement.id = "TitleEventPending"
                spanElement.textContent = element.title
                divElement3.appendChild(spanElement)
            });
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al obtener los eventos');
        });
});

function formatToReadableDate(dateStr) {
    // Intentar parsear la fecha con el constructor Date
    const date = new Date(dateStr);

    // Verificar si la fecha es válida
    if (isNaN(date)) {
        throw new Error('Fecha no válida');
    }

    // Obtener los componentes de la fecha
    const day = date.getDate().toString().padStart(2, '0'); // Día con dos dígitos
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Mes con dos dígitos
    const year = date.getFullYear(); // Año

    // Formatear como DD/MM/YYYY
    return `${day}/${month}/${year}`;
}