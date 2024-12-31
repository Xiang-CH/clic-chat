import {Input} from "@/components/ui/input"
import {MagnifyingGlassIcon} from "@radix-ui/react-icons";

export default async function Home({searchParams}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {

  const query = (await searchParams).q
  const res = await fetch(`http://localhost:5328/api/search?q=${query}`);
  const data = await res.json();
  console.log(data)

  return (
    <main className="w-full px-6 py-2">
      <div className="w-full max-w-sm relative">
        <MagnifyingGlassIcon className="w-4 h-4 absolute left-2.5 top-2.5 text-gray-500 dark:text-gray-400"/>
        <form action={`/search`} method="get">
          <Input type="search" placeholder="Search" className="pl-8" name="q" defaultValue={query}/>
        </form>
      </div>
      <section>
        {query && data.map((item, index) => (
          <a key={index} href={item.url} target="_blank">
            <div
              className="flex flex-col justify-start p-4 my-2 bg-white dark:bg-gray-800 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold">{item.cap_no}. {item.cap_title}</h3>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{item.text}</p>
              </div>
              <div>{item._relevance_score}</div>
            </div>
          </a>
        ))}
      </section>
    </main>
  )
}