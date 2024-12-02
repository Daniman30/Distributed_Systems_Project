import { dailyEvents } from "./event.js";

let date = new Date();
let year = date.getFullYear();
let month = date.getMonth();

const day = document.querySelector(".calendar-dates");
const currdate = document.querySelector(".calendar-current-date");
const prenexIcons = document.querySelectorAll(".calendar-navigation");

// Array of month names
const months = [
    "January", "February", "March", "April", "May",
    "June", "July", "August", "September", "October",
    "November", "December"
];

// Function to generate the calendar
export const manipulate = async () => {
    return new Promise(async (resolve, reject) => {
        try {
            let dayone = new Date(year, month, 1).getDay();
            let lastdate = new Date(year, month + 1, 0).getDate();
            let dayend = new Date(year, month, lastdate).getDay();
            let monthlastdate = new Date(year, month, 0).getDate();
            let lit = "";

            // Agregar las fechas del mes anterior
            for (let i = dayone; i > 0; i--) {
                lit += `<li class="inactive">${monthlastdate - i + 1}</li>`;
            }

            // Agregar las fechas del mes actual
            let promises = []; // Array para almacenar las promesas de `dailyEvents`
            for (let i = 1; i <= lastdate; i++) {
                let isToday = i === date.getDate()
                    && month === new Date().getMonth()
                    && year === new Date().getFullYear()
                    ? "active"
                    : "";

                let dayI = i < 10 ? `0${i}` : i;
                let listItem = `<li class="${isToday}" id="day-${year}-${month + 1}-${dayI}">${i}`;

                // Almacena las promesas de dailyEvents
                promises.push(
                    dailyEvents(`${year}-${month + 1}-${dayI}`).then(({ personalEvents }) => {
                        let eventsHTML = "";
                        personalEvents.forEach(event => {
                            eventsHTML += `<p class="event-title">${event.title}</p>`;
                        });
                        document.querySelector(`#day-${year}-${month + 1}-${dayI}`).innerHTML += eventsHTML;
                    }).catch(error => {
                        console.error('Error:', error.message);
                    })
                );

                lit += `${listItem}</li>`;
            }

            // Agregar las fechas del próximo mes
            for (let i = dayend; i < 6; i++) {
                lit += `<li class="inactive">${i - dayend + 1}</li>`;
            }

            currdate.innerText = `${months[month]} ${year}`;
            day.innerHTML = lit;

            // Esperar a que todas las promesas de dailyEvents se resuelvan
            await Promise.all(promises);

            // Resolver la promesa principal
            resolve();
        } catch (error) {
            console.error('Error en manipulate:', error);
            reject(error);
        }
    });
};


manipulate();

// Attach a click event listener to each icon
prenexIcons.forEach(icon => {

    // When an icon is clicked
    icon.addEventListener("click", () => {

        // Check if the icon is "calendar-prev"
        // or "calendar-next"
        month = icon.id === "calendar-prev" ? month - 1 : month + 1;

        // Check if the month is out of range
        if (month < 0 || month > 11) {

            // Set the date to the first day of the 
            // month with the new year
            date = new Date(year, month, new Date().getDate());

            // Set the year to the new year
            year = date.getFullYear();

            // Set the month to the new month
            month = date.getMonth();
        }

        else {

            // Set the date to the current date
            date = new Date();
        }

        // Call the manipulate function to 
        // update the calendar display
        manipulate();
    });
});

// Variables globales
const overlay = document.getElementById('overlay');
let activeMenu = null; // Para rastrear qué menú está activo

// Evento para abrir menús flotantes
document.querySelectorAll('.openMenu').forEach(button => {
    button.addEventListener('click', function (event) {
        event.preventDefault(); // Previene el comportamiento predeterminado del enlace

        // Identifica el menú a abrir
        const menuId = this.getAttribute('data-menu');
        const menu = document.getElementById(menuId);

        // Muestra el overlay y el menú flotante correspondiente
        if (menu) {
            overlay.style.display = 'flex';
            menu.style.display = 'flex';
            activeMenu = menu; // Guarda el menú activo
        }
    });
});

// Evento para cerrar menús
overlay.addEventListener('click', closeMenu);
document.querySelectorAll('.closeMenu').forEach(button => {
    button.addEventListener('click', closeMenu);
});

// Función para cerrar el menú flotante activo
export function closeMenu() {
    if (activeMenu) {
        activeMenu.style.display = 'none';
        overlay.style.display = 'none';
        activeMenu = null; // Reinicia el menú activo
    }
}