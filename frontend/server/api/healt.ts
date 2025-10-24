export default defineEventHandler(() => {
    return $fetch('http://localhost:8000/health')
})
