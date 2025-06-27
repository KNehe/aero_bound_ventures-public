import { FaMapMarkerAlt } from 'react-icons/fa';

const destinations = [
  {
    id: 1,
    name: 'Bali, Indonesia',
    description: 'Tropical paradise with pristine beaches and rich culture',
    image: '/aeroplane.jpg', // Using existing image as placeholder
    price: 'From $899',
    rating: 4.8
  },
  {
    id: 2,
    name: 'Santorini, Greece',
    description: 'Stunning sunsets and white-washed architecture',
    image: '/aeroplane.jpg', // Using existing image as placeholder
    price: 'From $1,299',
    rating: 4.9
  },
  {
    id: 3,
    name: 'Tokyo, Japan',
    description: 'Modern metropolis with ancient traditions',
    image: '/aeroplane.jpg', // Using existing image as placeholder
    price: 'From $1,199',
    rating: 4.7
  },
  {
    id: 4,
    name: 'New York, USA',
    description: 'The city that never sleeps with endless possibilities',
    image: '/aeroplane.jpg', // Using existing image as placeholder
    price: 'From $699',
    rating: 4.6
  }
];

export default function PopularDestinationsSection() {
  return (
    <section className="w-full bg-gray-100 py-20 px-4 md:px-0">
      <div className="max-w-5xl mx-auto text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-extrabold text-blue-900 mb-4">Popular Destinations</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Discover our most sought-after destinations and start planning your next adventure
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {destinations.map((destination) => (
          <div key={destination.id} className="bg-white rounded-2xl shadow-lg overflow-hidden transition-transform hover:-translate-y-2 hover:shadow-xl">
            <div className="relative h-48 overflow-hidden">
              <img 
                src={destination.image} 
                alt={destination.name}
                className="w-full h-full object-cover transition-transform hover:scale-110"
              />
              <div className="absolute bottom-3 left-3 bg-blue-600 text-white px-2 py-1 rounded-full text-sm font-semibold">
                {destination.price}
              </div>
            </div>
            <div className="p-6">
              <div className="flex items-center mb-2">
                <FaMapMarkerAlt className="text-blue-600 mr-2" />
                <h3 className="text-xl font-bold text-blue-900">{destination.name}</h3>
              </div>
              <p className="text-gray-600 text-sm mb-4">{destination.description}</p>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-yellow-500 mr-1">★</span>
                  <span className="text-sm font-semibold text-gray-700">{destination.rating}</span>
                </div>
              </div>
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors duration-200">
                Book Now
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
} 