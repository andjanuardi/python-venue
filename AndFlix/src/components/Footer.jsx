import { motion } from 'framer-motion'

const FOOTER_LINKS = [
  ['FAQ', 'Help Center', 'Account', 'Media Center'],
  ['Investor Relations', 'Jobs', 'Redeem Gift Cards', 'Buy Gift Cards'],
  ['Ways to Watch', 'Terms of Use', 'Privacy', 'Cookie Preferences'],
  ['Corporate Information', 'Contact Us', 'Speed Test', 'Legal Notices'],
]

export default function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      className="bg-netflix-black text-netflix-gray pt-12 pb-8 px-8 lg:px-16"
    >
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {FOOTER_LINKS.map((col, i) => (
            <div key={i} className="space-y-3">
              {col.map((link) => (
                <a
                  key={link}
                  href="#"
                  onClick={(e) => e.preventDefault()}
                  className="block text-sm hover:underline"
                >
                  {link}
                </a>
              ))}
            </div>
          ))}
        </div>

        <div className="border-t border-netflix-border pt-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm">
            &copy; {new Date().getFullYear()} AndFlix. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-netflix-red font-bold text-lg">AndFlix</span>
            <span className="text-netflix-gray-light">Powered by Loklok API</span>
          </div>
        </div>
      </div>
    </motion.footer>
  )
}
