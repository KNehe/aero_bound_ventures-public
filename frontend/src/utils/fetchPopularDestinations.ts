export async function fetchPopularDestinations(originCityCode: string, period: string) {
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/analytics/most-travelled-destinations?origin_city_code=${originCityCode}&period=${period}`
    const res = await fetch(
        url,
        {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
        }
    );
    if (!res.ok) {
        throw new Error("Failed to fetch popular destinations");
    }
    return res.json();
}
