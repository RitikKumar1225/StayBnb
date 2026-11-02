document.addEventListener("DOMContentLoaded", () => {
  const placeGrid = document.querySelector("[data-place-grid]");
  const showPlacesButton = document.querySelector("[data-show-places]");
  if (placeGrid && showPlacesButton) {
    const placeCards = [...placeGrid.querySelectorAll("[data-place-card]")];
    let expanded = false;

    function updateVisiblePlaces() {
      placeCards.forEach((card) => { card.hidden = false; });
      if (expanded) {
        showPlacesButton.textContent = "Show fewer places";
        showPlacesButton.hidden = false;
        return;
      }

      const rowTops = [...new Set(placeCards.map((card) => Math.round(card.getBoundingClientRect().top)))];
      const thirdRowTop = rowTops[2];
      const hiddenCards = thirdRowTop === undefined
        ? []
        : placeCards.filter((card) => Math.round(card.getBoundingClientRect().top) > thirdRowTop);
      hiddenCards.forEach((card) => { card.hidden = true; });
      showPlacesButton.hidden = hiddenCards.length === 0;
      showPlacesButton.textContent = "Show more places";
    }

    showPlacesButton.addEventListener("click", () => {
      expanded = !expanded;
      updateVisiblePlaces();
    });
    window.addEventListener("resize", updateVisiblePlaces);
    updateVisiblePlaces();
  }

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  const checkIn = document.querySelector('input[name="check_in"]');
  const checkOut = document.querySelector('input[name="check_out"]');
  if (checkIn && checkOut) {
    checkIn.addEventListener("change", () => {
      checkOut.min = checkIn.value;
      if (checkOut.value && checkOut.value <= checkIn.value) checkOut.value = "";
    });
  }

  const calendar = document.querySelector("[data-availability-calendar]");
  if (!calendar) return;

  const bookingForm = document.querySelector("[data-booking-form]");
  const checkInInput = bookingForm?.querySelector('input[name="check_in"]');
  const checkOutInput = bookingForm?.querySelector('input[name="check_out"]');
  const daysContainer = calendar.querySelector("[data-calendar-days]");
  const monthLabel = calendar.querySelector("[data-calendar-month]");
  const helpLabel = calendar.querySelector("[data-calendar-help]");
  const previousButton = calendar.querySelector("[data-calendar-prev]");
  const nextButton = calendar.querySelector("[data-calendar-next]");
  const checkInLabel = bookingForm?.querySelector("[data-checkin-label]");
  const checkOutLabel = bookingForm?.querySelector("[data-checkout-label]");
  const submitButton = bookingForm?.querySelector("[data-booking-submit]");
  const estimateLabel = bookingForm?.querySelector("[data-stay-estimate]");
  const guestInput = bookingForm?.querySelector('[name="guests"]');
  const todayValue = calendar.dataset.today;
  const today = new Date(`${todayValue}T00:00:00`);
  const todayMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const availability = JSON.parse(document.getElementById("property-availability").textContent);
  const unavailable = new Set();

  availability.forEach(({ check_in: checkIn, check_out: checkOut }) => {
    const date = new Date(`${checkIn}T00:00:00`);
    const lastNight = new Date(`${checkOut}T00:00:00`);
    while (date < lastNight) {
      unavailable.add(toIsoDate(date));
      date.setDate(date.getDate() + 1);
    }
  });

  let visibleMonth = new Date(todayMonth);
  let selectedCheckIn = checkInInput?.value || "";
  let selectedCheckOut = checkOutInput?.value || "";

  function toIsoDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function formatDate(value) {
    if (!value) return "Choose a date";
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" })
      .format(new Date(`${value}T00:00:00`));
  }

  function updateSelection() {
    if (!bookingForm) return;
    checkInInput.value = selectedCheckIn;
    checkOutInput.value = selectedCheckOut;
    checkInLabel.textContent = formatDate(selectedCheckIn);
    checkOutLabel.textContent = formatDate(selectedCheckOut);
    submitButton.disabled = !(selectedCheckIn && selectedCheckOut);

    if (selectedCheckIn && selectedCheckOut) {
      const nights = Math.round(
        (new Date(`${selectedCheckOut}T00:00:00`) - new Date(`${selectedCheckIn}T00:00:00`))
        / 86400000,
      );
      const nightlyPrice = Number(bookingForm.dataset.price);
      estimateLabel.textContent = `${nights} night${nights === 1 ? "" : "s"} · $${(nightlyPrice * nights).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} total`;
    } else {
      estimateLabel.textContent = "Choose dates to see your stay total.";
    }
  }

  function renderCalendar() {
    const year = visibleMonth.getFullYear();
    const month = visibleMonth.getMonth();
    monthLabel.textContent = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" })
      .format(visibleMonth);
    previousButton.disabled = visibleMonth <= todayMonth;
    daysContainer.replaceChildren();

    const firstWeekday = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cellCount = Math.ceil((firstWeekday + daysInMonth) / 7) * 7;
    for (let cell = 0; cell < cellCount; cell += 1) {
      const dayNumber = cell - firstWeekday + 1;
      if (dayNumber < 1 || dayNumber > daysInMonth) {
        const pad = document.createElement("span");
        pad.className = "calendar-pad";
        pad.setAttribute("aria-hidden", "true");
        daysContainer.append(pad);
        continue;
      }

      const date = new Date(year, month, dayNumber);
      const dateValue = toIsoDate(date);
      const isPast = dateValue < todayValue;
      const isBooked = unavailable.has(dateValue);
      const isSelected = dateValue === selectedCheckIn || dateValue === selectedCheckOut;
      const isInRange = selectedCheckIn && selectedCheckOut
        && dateValue > selectedCheckIn && dateValue < selectedCheckOut;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "calendar-day";
      button.textContent = String(dayNumber);
      button.dataset.date = dateValue;
      button.setAttribute("aria-label", formatDate(dateValue));
      if (isPast) button.classList.add("is-past");
      if (isBooked) button.classList.add("is-booked");
      if (isSelected) button.classList.add("is-selected");
      if (isInRange) button.classList.add("is-in-range");
      button.setAttribute("aria-pressed", String(Boolean(isSelected)));
      button.disabled = isPast || isBooked || !bookingForm;
      if (!isPast && !isBooked && bookingForm) {
        button.addEventListener("click", () => {
          if (!selectedCheckIn || selectedCheckOut || dateValue <= selectedCheckIn) {
            selectedCheckIn = dateValue;
            selectedCheckOut = "";
            helpLabel.textContent = "Now choose your check-out date.";
          } else {
            const rangeHasUnavailableNight = [...unavailable]
              .some((unavailableDate) => unavailableDate >= selectedCheckIn && unavailableDate < dateValue);
            if (rangeHasUnavailableNight) {
              selectedCheckIn = dateValue;
              selectedCheckOut = "";
              helpLabel.textContent = "Those dates cross a booked stay. Choose a different check-out.";
            } else {
              selectedCheckOut = dateValue;
              helpLabel.textContent = "Dates look good. Send a booking request when you’re ready.";
            }
          }
          updateSelection();
          renderCalendar();
        });
      }
      daysContainer.append(button);
    }
    nextButton.disabled = false;
  }

  previousButton.addEventListener("click", () => {
    visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
    renderCalendar();
  });
  nextButton.addEventListener("click", () => {
    visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
    renderCalendar();
  });

  if (bookingForm) {
    if (selectedCheckIn && selectedCheckOut) {
      helpLabel.textContent = "Review your dates or select another stay.";
    } else if (selectedCheckIn) {
      helpLabel.textContent = "Now choose your check-out date.";
    }
    updateSelection();
  }
  renderCalendar();
});
