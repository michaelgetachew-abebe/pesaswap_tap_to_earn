document.addEventListener("DOMContentLoaded", () => {
    // Step navigation
    const steps = document.querySelectorAll(".step")
    const stepContents = document.querySelectorAll(".step-content")
    const prevBtn = document.getElementById("prev-btn")
    const nextBtn = document.getElementById("next-btn")
    const progressBar = document.getElementById("progress")
  
    let currentStep = 1
    const totalSteps = steps.length
  
    // Initialize progress bar
    updateProgressBar()
  
    // Next button click
    nextBtn.addEventListener("click", () => {
      if (currentStep < totalSteps) {
        goToStep(currentStep + 1)
      }
    })
  
    // Previous button click
    prevBtn.addEventListener("click", () => {
      if (currentStep > 1) {
        goToStep(currentStep - 1)
      }
    })
  
    // Go to specific step
    function goToStep(stepNumber) {
      // Update active step
      document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove("active")
      document.querySelector(`.step[data-step="${stepNumber}"]`).classList.add("active")
  
      // Mark previous steps as completed
      for (let i = 1; i < stepNumber; i++) {
        document.querySelector(`.step[data-step="${i}"]`).classList.add("completed")
      }
  
      // Remove completed class from future steps
      for (let i = stepNumber; i <= totalSteps; i++) {
        document.querySelector(`.step[data-step="${i}"]`).classList.remove("completed")
      }
  
      // Update active content
      document.querySelector(`.step-content.active`).classList.remove("active")
      document.getElementById(`step-${stepNumber}`).classList.add("active")
  
      // Update current step
      currentStep = stepNumber
  
      // Update buttons state
      updateButtonsState()
  
      // Update progress bar
      updateProgressBar()
    }
  
    // Update buttons state based on current step
    function updateButtonsState() {
      prevBtn.disabled = currentStep === 1
  
      if (currentStep === totalSteps) {
        nextBtn.textContent = "Finish"
      } else {
        nextBtn.textContent = "Next"
      }
    }
  
    // Update progress bar
    function updateProgressBar() {
      const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100
      progressBar.style.width = `${progressPercentage}%`
    }
  
    // Accordion functionality
    const accordionHeaders = document.querySelectorAll(".accordion-header")
  
    accordionHeaders.forEach((header) => {
      header.addEventListener("click", function () {
        const accordionItem = this.parentElement
        accordionItem.classList.toggle("active")
      })
    })
  
    // Initialize first accordion as open
    document.querySelector(".accordion-item").classList.add("active")
    document.querySelector(".accordion-content").style.maxHeight =
      document.querySelector(".accordion-content").scrollHeight + "px"
  })
  
  