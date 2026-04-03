/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { useState, onMounted, onWillUnmount } from "@odoo/owl";

const STORAGE_KEY = "chatter_visibility_preferences";

// Shared state for chatter preferences
const chatterPreferences = {
    visible: true,
    position: "right", // "right" or "bottom"
};

// Load preferences from localStorage
function loadPreferences() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            const prefs = JSON.parse(stored);
            chatterPreferences.visible = prefs.visible !== undefined ? prefs.visible : true;
            chatterPreferences.position = prefs.position || "right";
        }
    } catch (e) {
        // Silently fail - use defaults
    }
}

// Save preferences to localStorage
function savePreferences() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chatterPreferences));
    } catch (e) {
        // Silently fail
    }
}

// Load preferences on module init
loadPreferences();

// Patch FormRenderer to override mailLayout function
patch(FormRenderer.prototype, {
    /**
     * Override mailLayout to respect user preference
     * This method is called by Odoo to determine the chatter layout
     */
    mailLayout(hasAttachmentContainer) {
        const originalLayout = super.mailLayout(hasAttachmentContainer);

        // If user prefers bottom, force BOTTOM_CHATTER variants
        if (chatterPreferences.position === "bottom") {
            // Map all side layouts to bottom layouts
            switch (originalLayout) {
                case "SIDE_CHATTER":
                    return "BOTTOM_CHATTER";
                case "EXTERNAL_COMBO_XXL":
                    return "EXTERNAL_COMBO";
                case "EXTERNAL_SIDE_CHATTER":
                    return "BOTTOM_CHATTER";
                default:
                    // If already a bottom layout, keep it
                    return originalLayout;
            }
        }

        // If user prefers right, ensure we use side layouts
        if (chatterPreferences.position === "right") {
            // Map bottom layouts back to side layouts if needed
            switch (originalLayout) {
                case "BOTTOM_CHATTER":
                    return "SIDE_CHATTER";
                case "EXTERNAL_COMBO":
                    return "EXTERNAL_COMBO_XXL";
                default:
                    return originalLayout;
            }
        }

        return originalLayout;
    },
});

// Patch FormController to add control buttons
patch(FormController.prototype, {
    setup() {
        super.setup();

        this.chatterState = useState({
            visible: chatterPreferences.visible,
            position: chatterPreferences.position,
            hasChatter: false,
        });

        onMounted(() => {
            // Apply initial state immediately
            this.applyChatterState();
            
            // Then check for chatter
            this.checkAndApplyChatter();

            // Watch for DOM changes to detect chatter appearance
            this.chatterObserver = new MutationObserver(() => {
                this.checkAndApplyChatter();
            });

            const target = document.querySelector('.o_content') || document.body;
            this.chatterObserver.observe(target, {
                childList: true,
                subtree: true,
            });
            
            // Also apply state after a short delay to catch late-rendered chatter
            setTimeout(() => {
                this.applyChatterState();
            }, 100);
        });

        onWillUnmount(() => {
            if (this.chatterObserver) {
                this.chatterObserver.disconnect();
            }
        });
    },

    /**
     * Check for chatter and apply state
     */
    checkAndApplyChatter() {
        const chatter = document.querySelector(".o-mail-Form-chatter");
        const hasChatter = !!chatter;

        if (this.chatterState.hasChatter !== hasChatter) {
            this.chatterState.hasChatter = hasChatter;
        }

        if (hasChatter) {
            this.applyChatterState();
        }
    },

    /**
     * Apply visibility and position classes to DOM
     */
    applyChatterState() {
        const formView = document.querySelector(".o_form_view");

        if (!formView) {
            return;
        }

        // Toggle visibility - use explicit add/remove for reliability
        if (this.chatterState.visible) {
            formView.classList.remove("chatter-hidden");
        } else {
            formView.classList.add("chatter-hidden");
        }

        // Set position by adding class to form view
        if (this.chatterState.position === "right") {
            formView.classList.remove("chatter-position-bottom");
            
            const formRenderer = document.querySelector('.o_form_renderer');
            if (formRenderer) {
                // When chatter is hidden at right position, remove h-100 to allow full width
                // When chatter is visible at right position, restore h-100 for side-by-side layout
                if (this.chatterState.visible) {
                    // Restore h-100 class when chatter is visible (side-by-side layout)
                    if (!formRenderer.classList.contains('h-100')) {
                        formRenderer.classList.add('h-100');
                    }
                } else {
                    // Remove h-100 class when chatter is hidden (full width layout)
                    formRenderer.classList.remove('h-100');
                }
            }
        } else {
            formView.classList.add("chatter-position-bottom");
            
            // CRITICAL FIX - Remove h-100 class from .o_form_renderer
            // This allows it to grow beyond viewport height and enable scrolling
            const formRenderer = document.querySelector('.o_form_renderer');
            if (formRenderer) {
                formRenderer.classList.remove('h-100');
            }
        }

        // Force browser reflow to ensure CSS changes are applied
        void formView.offsetHeight;
    },

    /**
     * Toggle chatter visibility
     */
    toggleChatterVisibility() {
        this.chatterState.visible = !this.chatterState.visible;
        chatterPreferences.visible = this.chatterState.visible;
        savePreferences();
        
        // Apply state immediately
        this.applyChatterState();
        
        // Force re-render to update template (dropdown visibility)
        this.render();
    },

    /**
     * Change chatter position
     * Uses CSS to force layout change immediately
     */
    async setChatterPosition(position) {
        const oldPosition = this.chatterState.position;
        
        // Update state and preferences FIRST (before any re-render)
        this.chatterState.position = position;
        chatterPreferences.position = position;
        savePreferences();

        // Force re-render by reloading the model
        // This will trigger FormRenderer to re-render with new mailLayout()
        if (oldPosition !== position && this.model && this.model.root) {
            try {
                await this.model.root.load();
            } catch (error) {
                // Silently fail - CSS will handle the layout
            }
        }

        // Apply CSS class as backup
        this.applyChatterState();
    },

    /**
     * Get icon for current visibility state
     * Using eye icons for better visibility toggle indication
     */
    get chatterVisibilityIcon() {
        return this.chatterState.visible ? "fa-comment" : "fa-eye-slash";
    },

    /**
     * Check if chatter exists
     */
    get hasChatter() {
        return this.chatterState.hasChatter;
    },
});
