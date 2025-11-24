// Capitalize
export function capitalize(str: string): string {
    if (str.length === 0) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Uncapitalize
export function uncapitalize(str: string): string {
    if (str.length === 0) return str;
    return str.charAt(0).toLowerCase() + str.slice(1);
}