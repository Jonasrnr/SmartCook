window.initRecipeEdit = function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ?.value;
    const recipeIdElem = document.getElementById('recipe-id');
    if (!recipeIdElem) return;
    const recipeId = JSON.parse(recipeIdElem.textContent);

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
                    const list = document.getElementById("instruction-list");
                    if (list) {
                        list.querySelectorAll(".step-number").forEach((el, idx) => {
                            el.dataset.step = idx + 1;
                        });
                    }
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
                    newLi.className = "grid grid-cols-12 gap-2";
                    newLi.dataset.ingredientId = data.id;
                    newLi.innerHTML = `
                    <input type="text" value="" data-id="${data.id}" data-field="quantity" data-type="ingredient" class="auto-save-input col-span-3 border-gray-100 rounded-lg px-2 py-1.5 text-xs focus:ring-2 focus:ring-indigo-100" placeholder="-">
                    <input type="text" value="" data-id="${data.id}" data-field="unit" data-type="ingredient" class="auto-save-input col-span-3 border-gray-100 rounded-lg px-2 py-1.5 text-xs focus:ring-2 focus:ring-indigo-100" placeholder="-">
                    <input type="text" value="" data-id="${data.id}" data-field="name" data-type="ingredient" class="auto-save-input col-span-6 border-gray-100 rounded-lg px-2 py-1.5 text-xs focus:ring-2 focus:ring-indigo-100 font-medium" placeholder="-">
                `;
                    list.appendChild(newLi);
                    newLi.querySelectorAll(".auto-save-input").forEach(input => input.addEventListener("change", handleAutoSave));
                    newLi.querySelector('input').focus();
                } else {
                    const list = document.getElementById("instruction-list");
                    const newDiv = document.createElement("div");
                    newDiv.className = "relative pl-10 group";
                    newDiv.dataset.instructionId = data.id;
                    newDiv.innerHTML = `
                    <div class="absolute left-0 top-0 w-7 h-7 bg-gray-50 rounded-full flex items-center justify-center font-bold text-black group-focus-within:bg-indigo-600 group-focus-within:text-white transition-all">
                        <span class="step-number text-[10px]" data-step="${data.step_number}"></span>
                    </div>
                    <textarea data-id="${data.id}" data-field="description" data-type="instruction" class="auto-save-input w-full border-gray-100 focus:ring-4 focus:ring-indigo-50/50 rounded-xl p-3 text-sm text-gray-700 shadow-sm transition-all resize-none" placeholder="Schritt beschreiben..." rows="3"></textarea>
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