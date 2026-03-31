import { apiClient } from "@/lib/api";

type Destination = {
  destination: string;
  analytics: {
    flights: { score: number };
    travelers: { score: number };
  };
};

export async function fetchPopularDestinations(originCityCode: string, period: string) {
  return apiClient.get<Destination[]>("/analytics/most-travelled-destinations", {
    params: {
      origin_city_code: originCityCode,
      period,
    },
  });
}
