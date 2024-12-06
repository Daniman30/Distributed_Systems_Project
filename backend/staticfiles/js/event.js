
import {manipulate} from './calendar.js';

const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
const userData = localStorage.getItem('userData') || sessionStorage.getItem('userData');
const user = JSON.parse(userData);

// Variables globales
const overlay = document.getElementById('overlay');
let activeMenu = null; // Para rastrear qué menú está activo
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
    const participantsEvent = `${document.getElementById('EventParticipants').value}, ${user.id}`;

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

    const dataF = Object.fromEntries(Object.entries(rawData).filter(([_, value]) => value !== null));
    console.log("userdata", user)

    try {
        // Enviar los datos al endpoint
        const response = await fetch('http://127.0.0.1:8000/api/events/create/', {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`,
            },
            body: JSON.stringify(dataF),
            
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

// View Event
async function viewEvent(idEvent) {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/events/pending/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`,
            },
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(`Error al obtener eventos: ${err.detail || err}`);
        }

        const data = await response.json();
        console.log("data", data)
        const EventFinal = data.find(event => event.id === idEvent);

        if (!EventFinal) {
            throw new Error(`El evento con ID ${idEvent} no se encontró.`);
        }

        return EventFinal;
    } catch (error) {
        console.error('Error:', error.message);
        alert('Hubo un error al obtener los eventos');
        throw error; // Re-lanzar el error para manejarlo en la llamada
    }
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
            menuEvent.innerHTML = ''

            const eventH6 = document.createElement('h6');
            eventH6.className = "dropdown-header"
            eventH6.textContent = "Events Pending"
            menuEvent.appendChild(eventH6)


            data.forEach(element => {
                const Aelement = document.createElement('a');
                Aelement.classList = ["dropdown-item d-flex align-items-center"];
                Aelement.id = "Aelement"
                Aelement.setAttribute('data-menu', "menu9")

                Aelement.addEventListener('click', function (event) {
                    event.preventDefault(); // Previene el comportamiento predeterminado del enlace
                    
                    viewEvent(element.id)
                        .then(eventDataFunc => {
                            const eventData = eventDataFunc

                            const eventTitle = document.getElementById('EventTitle');
                            eventTitle.textContent = eventData.title;

                            const descriptionEvent = document.getElementById('descriptionEvent');
                            descriptionEvent.textContent = eventData.description

                            const startTimeEvent = document.getElementById('startTimeEvent');
                            startTimeEvent.textContent = eventData.start_time

                            const endTimeEvent = document.getElementById('endTimeEvent');
                            endTimeEvent.textContent = eventData.end_time

                            const privacyEvent = document.getElementById('privacyEvent');
                            privacyEvent.textContent = eventData.privacy

                            const idEventText = document.getElementById('idEvent');
                            idEventText.textContent = eventData.id

                            const groupIdEvent = document.getElementById('groupIdEvent');
                            adminEvent.groupIdEvent = eventData.group

                            const participantIdsEvent = document.getElementById('participantIdsEvent');
                            participantIdsEvent.textContent = eventData.participants

                            const confirmedParticipantsEvent = document.getElementById('confirmedParticipantsEvent');
                            confirmedParticipantsEvent.textContent = eventData.accepted_by
                        
                            // Identifica el menú a abrir
                            const menuId = this.getAttribute('data-menu');
                            const menu = document.getElementById(menuId);

                            // Muestra el overlay y el menú flotante correspondiente
                            if (menu) {
                                overlay.style.display = 'flex';
                                menu.style.display = 'flex';
                                activeMenu = menu; // Guarda el menú activo
                            }

                            // Evento para cerrar menús
                            overlay.addEventListener('click', closeMenu);
                            document.querySelectorAll('.closeMenu').forEach(button => {
                                button.addEventListener('click', closeMenu);
                            });
                        })
                        .catch(error => {
                            console.error('Error al obtener el evento:', error.message);
                        });                    
                });

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
                divElement4.textContent = `id ${element.id} - date: ${formatToReadableDate(element.start_time)}`
                divElement3.appendChild(divElement4)

                const spanElement = document.createElement('span');
                spanElement.className = "font-weight-bold"
                spanElement.id = "TitleEventPending"
                spanElement.textContent = element.title
                divElement3.appendChild(spanElement)

                
            });
            const CountEventsPending = document.getElementById('CountEventsPending')
            CountEventsPending.textContent = data.length
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

function closeMenu() {
    if (activeMenu) {
        activeMenu.style.display = 'none';
        overlay.style.display = 'none';
        activeMenu = null; // Reinicia el menú activo
    }
}

document.getElementById('acceptBtn').addEventListener('click', function () {
    const idEventUrl =  document.getElementById('idEvent')
    return fetch(`http://127.0.0.1:8000/api/events/${idEventUrl.textContent}/accept/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
        },
        body: {},
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al aceptar evento: ${err.detail || err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(data)
            manipulate()
            closeMenu()
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al aceptar el evento');
        });
});

document.getElementById('declineBtn').addEventListener('click', function () {
    const idEventUrl =  document.getElementById('idEvent')
    console.log("Evento a cancelar", idEventUrl.textContent)
    fetch(`http://127.0.0.1:8000/api/events/${idEventUrl.textContent}/cancel/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`, // Token para autenticación
        },
        body: {},
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(`Error al rechazar el evento: ${err}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(data)
            closeMenu()
        })
        .catch(error => {
            // Manejar errores
            console.error('Error:', error.message);
            alert('Hubo un error al rechazar el evento');
        });
});

document.getElementsByClassName("event-title").addEventListener('click', function() {

});