import type { ComputedRef, Ref } from "vue";
import { createContext } from "reka-ui";

export interface SortingState<T> {
    key: keyof T;
    direction: "asc" | "desc";
}

export interface Column<T> {
    key: keyof T;
    label: string;
}

export interface DataTableContext<T> {
    index: keyof T;
    columns: ComputedRef<Column<T>[]>;
    data: ComputedRef<T[]>;
    sortedData: ComputedRef<T[]>;
    sorting: Ref<SortingState<T>>;
    toggleSorting: (key: keyof T) => void;
    pageSize: number;
    container: Ref<HTMLElement | null>;
}

const [_useDataContext, _provideDataContext] =
    createContext<DataTableContext<unknown>>("DataTable");

const [_useDataItemsContext, _provideDataItemsContext] =
    createContext<ComputedRef<unknown[]>>("DataTableItems");

export function useDataTableContext<T>() {
    return _useDataContext() as DataTableContext<T>;
}

export function provideDataTableContext<T>(context: DataTableContext<T>) {
    _provideDataContext(context as DataTableContext<unknown>);
}

export function useDataTableItemsContext<T>() {
    return _useDataItemsContext() as ComputedRef<T[]>;
}

export function provideDataTableItemsContext<T>(context: ComputedRef<T[]>) {
    _provideDataItemsContext(context as ComputedRef<unknown[]>);
}
