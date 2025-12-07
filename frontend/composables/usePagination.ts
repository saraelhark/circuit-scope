import { ref, computed, type Ref } from 'vue'

export interface PaginationOptions {
    pageSize?: number
    initialPage?: number
}

export function usePagination(
    totalItems: Ref<number>,
    options: PaginationOptions = {}
) {
    const pageSize = ref(options.pageSize ?? 10)
    const currentPage = ref(options.initialPage ?? 1)

    const totalPages = computed(() => {
        if (totalItems.value <= 0) return 1
        return Math.max(1, Math.ceil(totalItems.value / pageSize.value))
    })

    const canPrevious = computed(() => currentPage.value > 1)
    const canNext = computed(() => currentPage.value < totalPages.value)

    function goToPrevious() {
        if (canPrevious.value) {
            currentPage.value -= 1
        }
    }

    function goToNext() {
        if (canNext.value) {
            currentPage.value += 1
        }
    }

    function goToPage(page: number) {
        if (page >= 1 && page <= totalPages.value) {
            currentPage.value = page
        }
    }

    function paginateArray<T>(items: T[]): T[] {
        const start = (currentPage.value - 1) * pageSize.value
        return items.slice(start, start + pageSize.value)
    }

    return {
        currentPage,
        pageSize,
        totalPages,
        canPrevious,
        canNext,
        goToPrevious,
        goToNext,
        goToPage,
        paginateArray
    }
}
