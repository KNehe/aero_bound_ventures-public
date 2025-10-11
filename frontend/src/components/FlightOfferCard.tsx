import { FaPlane } from 'react-icons/fa';
import { FlightOffer, Segment} from "@/types/flight_offer"
import useFlights from '@/store/flights';
import { useRouter } from 'next/navigation'


export default function FlightOfferCard({ flight }: { flight: FlightOffer }) {
  const { itineraries, price } = flight;
  const there = itineraries[0].segments;
  const back = itineraries.length > 1 ? itineraries[1].segments : null;
  const selectFlight = useFlights(state => state.selectFlight);
  const router = useRouter()

  const formatTime = (datetime: string) => new Date(datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formatDate = (datetime: string) => new Date(datetime).toLocaleDateString([], { month: 'short', day: 'numeric' });

  const renderSegment = (segment: Segment, isLast: boolean) => (
    <div key={segment.id} className={`flex items-center gap-2 ${!isLast ? 'mb-2' : ''}`}>
      <FaPlane className="text-blue-500" />
      <div className="text-sm">
        <span className="font-semibold">{segment.departure.iataCode}</span> {formatTime(segment.departure.at)} - <span className="font-semibold">{segment.arrival.iataCode}</span> {formatTime(segment.arrival.at)}
      </div>
      <div className="text-xs text-gray-500">{segment.carrierCode} {segment.number}</div>
    </div>
  );

  const onSelectFlight = () => {
    selectFlight(flight)
    router.push(`/flights/${flight.id}/`)
  }

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden mb-6 transition-transform hover:scale-105 text-black">
      <div className="p-4 border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold text-lg text-black">{there[0].departure.iataCode} to {there[there.length - 1].arrival.iataCode}</h3>
            <div className="text-sm text-black">
              <div>{formatDate(there[0].departure.at)}</div>
              {back && back.length > 0 && (
                <div className="text-sm text-black">Return: {formatDate(back[0].departure.at)}</div>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="font-extrabold text-2xl text-blue-600">${price.total}</div>
            <div className="text-xs text-black">Total price for all passengers</div>
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-md mb-2 border-b pb-1">Departure</h4>
            {there.map((segment, index) => renderSegment(segment, index === there.length - 1))}
          </div>
          {back && (
            <div>
              <h4 className="font-semibold text-md mb-2 border-b pb-1">Return</h4>
              {back.map((segment, index) => renderSegment(segment, index === back.length - 1))}
            </div>
          )}
        </div>
      </div>
      <div className="bg-blue-50 p-4 text-right">
        <button 
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors hover:cursor-pointer"
          onClick={onSelectFlight}
        >
          Select Flight
        </button>
      </div>
    </div>
  );
}
