export function initRecipeEdit() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ?.value;
    const recipeIdElem = document.getElementById('recipe-id');
    const recipeId = JSON.parse(recipeIdElem.textContent);

    // --- HILFSFUNKTIONEN ---
    function getStepEmoji(number) {
        const emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"];
        return (number > 0 && number <= emojis.length) ? emojis[number - 1] : "🔹";
    }

    function setInitialStepEmojis() {
        document.querySelectorAll('.step-number').forEach(span => {
            const step = parseInt(span.dataset.step, 10);
            span.textContent = getStepEmoji(step);
        });
    }

    function autoResizeTextarea() {
        this.style.height = "auto";
        this.style.height = `${this.scrollHeight}px`;
    }

    async function handleAutoSave(event) {
        const el = event.target;
        const { id, field, type } = el.dataset;
        const value = el.value;
        if (!id || !field || !type) return;

        let url;
        switch (type) {
            case "recipe":
                url = `/update_recipe/`;
                break;
            case "ingredient":
                url = `/update_ingredient/`;
                break;
            case "instruction":
                url = `/update_instruction/`;
                break;
            default:
                console.error("Unbekannter Auto-Save-Typ:", type);
                return;
        }

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                body: JSON.stringify({ id, field, value })
            });
            const data = await response.json();

            if (data.status === "ok") {
                el.classList.add("ring-2", "ring-green-400");
                setTimeout(() => el.classList.remove("ring-2", "ring-green-400"), 1000);
            } else if (data.status === "deleted") {
                const elementToRemove = el.closest(`[data-${type}-id="${data.id}"]`);
                if (elementToRemove) elementToRemove.remove();
                if (data.renumber) {
                    location.reload();
                }
            } else {
                throw new Error(data.message || "Unknown error");
            }
        } catch (err) {
            console.error("Fehler beim Speichern:", err);
            el.classList.add("ring-2", "ring-red-400");
            setTimeout(() => el.classList.remove("ring-2", "ring-red-400"), 1500);
        }
    }

    async function addNewItem(type) {
        const url = type === 'ingredient' ? `/add_ingredient/${recipeId}/` : `/add_instruction/${recipeId}/`;
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken, "Content-Type": "application/json" }
            });
            const data = await response.json();

            if (data.status === "ok") {
                if (type === 'ingredient') {
                    const list = document.getElementById("ingredient-list");
                    const newLi = document.createElement("li");
                    newLi.className = "flex gap-2 items-center";
                    newLi.dataset.ingredientId = data.id;
                    newLi.innerHTML = `
                    <input type="text" data-id="${data.id}" data-field="name" data-type="ingredient" class="auto-save-input border rounded px-2 py-1 w-32" placeholder="Name">
                    <input type="text" data-id="${data.id}" data-field="quantity" data-type="ingredient" class="auto-save-input border rounded px-2 py-1 w-20" placeholder="Menge" inputmode="numeric" pattern="[0-9]*">
                    <input type="text" data-id="${data.id}" data-field="unit" data-type="ingredient" class="auto-save-input border rounded px-2 py-1 w-20" placeholder="Einheit">
                `;
                    list.appendChild(newLi);
                    newLi.querySelectorAll(".auto-save-input").forEach(input => input.addEventListener("change", handleAutoSave));
                    newLi.querySelector('input').focus();
                } else {
                    const list = document.getElementById("instruction-list");
                    const newDiv = document.createElement("div");
                    newDiv.className = "bg-white p-3 flex gap-2 items-start";
                    newDiv.dataset.instructionId = data.id;
                    newDiv.innerHTML = `
                    <span class="font-bold text-3xl mt-1 step-number" data-step="${data.step_number}">${getStepEmoji(data.step_number)}</span>
                    <textarea data-id="${data.id}" data-field="description" data-type="instruction" class="overflow-y-auto resize-none auto-save-input shadow-xl rounded px-2 py-1 w-full" placeholder="Schritt Beschreibung"></textarea>
                `;
                    list.appendChild(newDiv);
                    const newTextarea = newDiv.querySelector("textarea");
                    newTextarea.addEventListener("input", autoResizeTextarea);
                    newTextarea.addEventListener("change", handleAutoSave);
                    newTextarea.focus();
                }
            } else {
                throw new Error(data.message || "Failed to add item");
            }
        } catch (err) {
            console.error(`Fehler beim Hinzufügen von ${type}:`, err);
        }
    }

    // --- INITIALISIERUNG & EVENT LISTENERS ---

    // Auto-resize für alle Textareas
    document.querySelectorAll("textarea.auto-save-input").forEach(textarea => {
        textarea.style.height = `${textarea.scrollHeight}px`;
        textarea.addEventListener("input", autoResizeTextarea);
    });

    // Auto-save für alle Inputs
    document.querySelectorAll(".auto-save-input").forEach(input => {
        input.addEventListener("change", handleAutoSave);
    });

    // Emojis für Schritte setzen
    setInitialStepEmojis();

    // "Hinzufügen"-Buttons
    const addIngredientBtn = document.getElementById("add-ingredient-btn");
    if (addIngredientBtn) {
        addIngredientBtn.addEventListener("click", () => addNewItem('ingredient'));
    }

    const addInstructionBtn = document.getElementById("add-instruction-btn");
    if (addInstructionBtn) {
        addInstructionBtn.addEventListener("click", () => addNewItem('instruction'));
    }
};