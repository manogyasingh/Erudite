"use client"

import { useState, useRef, useEffect } from "react"
import { Button, Card } from "@radix-ui/themes"
import { PaperclipIcon, SendIcon } from "lucide-react"

interface LLMInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  placeholder: string;
  disabled?: boolean;
}

export default function LLMInput({ value, onChange, handleSubmit, placeholder, disabled }: LLMInputProps) {
  const [files, setFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  useEffect(() => {
    adjustTextareaHeight()
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault() // Prevent new line
      handleSubmit(e as any) // Call handleSubmit
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card className="p-4">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={textareaRef}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onKeyDown={handleKeyDown}
            className="w-full resize-none overflow-hidden bg-transparent focus:border-0 outline-none text-foreground"
            rows={1}
            style={{ minHeight: '60px', paddingRight: '80px' }}
            disabled={disabled}
          />

          <div className="absolute bottom-2 right-2 flex items-center space-x-2">
            <Button
              type="button"
              variant="ghost"
              size="2"
              className="h-8 w-8"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
            >
              <PaperclipIcon className="h-4 w-4" />
            </Button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple
              className="hidden"
              disabled={disabled}
            />
            <Button 
              type="submit"
              size="2"
              className="h-8 w-8"
              disabled={disabled}
            >
              <SendIcon className="h-4 w-4" />
            </Button>
          </div>
        </form>
        {files.length > 0 && (
          <div className="mt-2 text-sm text-muted-foreground">
            {files.length} file(s) attached
          </div>
        )}
      </Card>
    </div>
  )
}