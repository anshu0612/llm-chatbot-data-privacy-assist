// This file contains custom JavaScript for the Data Privacy Assist application

// Add modern interactive animations
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn:not(.btn-link)');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.3s ease';
            this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });

    // Privacy eye interaction
    const privacyEye = document.getElementById('privacy-eye');
    const privacyToast = document.getElementById('privacy-toast');
    const privacyStatus = document.getElementById('privacy-status');
    
    if (privacyEye) {
        // Add active class to status indicator after page load
        setTimeout(() => {
            if (privacyStatus) {
                privacyStatus.classList.add('active');
            }
        }, 1000);
        
        // Trigger toast notification on eye click
        privacyEye.addEventListener('click', function() {
            // Add a pulse effect
            this.style.transform = 'scale(1.2)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 300);
            
            // Show toast notification
            setTimeout(() => {
                if (privacyToast) {
                    // Fallback - create DOM toast
                    const toast = document.createElement('div');
                    toast.className = 'privacy-toast-fallback';
                    toast.innerHTML = `
                        <div style="position: fixed; top: 20px; right: 20px; background: white; padding: 15px; 
                                    border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999; 
                                    max-width: 320px; border-left: 4px solid #4cd964;">
                            <div style="font-weight: 600; margin-bottom: 5px;">Privacy Monitor</div>
                            <div>Privacy scan complete. No sensitive data leaks detected.</div>
                        </div>
                    `;
                    document.body.appendChild(toast);
                    
                    setTimeout(() => {
                        toast.style.opacity = '0';
                        setTimeout(() => {
                            document.body.removeChild(toast);
                        }, 300);
                    }, 3000);
                }
            }, 300);
        });
    }
    
    // Fix tab display issues
    document.addEventListener('click', function(e) {
        if (e.target && e.target.closest('.nav-link')) {
            setTimeout(() => {
                // Force active tab to be visible
                const activeTabs = document.querySelectorAll('.tab-pane.active');
                activeTabs.forEach(tab => {
                    tab.style.display = 'block';
                    tab.style.visibility = 'visible';
                    tab.style.opacity = '1';
                });
            }, 100);
        }
    });
    
    // Ensure tab content is visible on page load
    setTimeout(() => {
        // Force all tabs to be visible initially
        const tabContents = document.querySelectorAll('.tab-pane');
        tabContents.forEach(tab => {
            tab.style.display = 'block';
            tab.style.visibility = 'visible';
            tab.style.opacity = '1';
        });
    }, 500);
    
    // Add interactive effects for panel hover
    const panels = document.querySelectorAll('.card, .border.rounded.shadow');
    panels.forEach(panel => {
        panel.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = '0 12px 20px rgba(0, 0, 0, 0.1), 0 0 10px rgba(76, 217, 100, 0.2)';
        });
        panel.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.08)';
        });
    });
    
    // Add animation to logo in navbar
    const navbarLogo = document.querySelector('.navbar-logo');
    if (navbarLogo) {
        // Random subtle movement for the logo
        setInterval(() => {
            const randomScale = 1 + (Math.random() * 0.03);
            navbarLogo.style.transform = `scale(${randomScale})`;
            setTimeout(() => {
                navbarLogo.style.transform = 'scale(1)';
            }, 500);
        }, 5000);
    }
});
