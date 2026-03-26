import * as React from "react"
import { format, parse, isValid } from "date-fns"
import { CalendarIcon, Clock, X } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DateTimePickerProps {
  value?: string | null
  onChange: (value: string | null) => void
  mode?: "datetime" | "date" | "time"
  required?: boolean
  hasError?: boolean
  id?: string
}

function parseISOSafe(val: string | null | undefined): Date | null {
  if (!val) return null
  const d = new Date(val)
  return isValid(d) ? d : null
}

export function DateTimePicker({
  value,
  onChange,
  mode = "datetime",
  required,
  hasError,
  id,
}: DateTimePickerProps) {
  const [open, setOpen] = React.useState(false)
  const date = parseISOSafe(value)

  const showDate = mode === "datetime" || mode === "date"
  const showTime = mode === "datetime" || mode === "time"

  const hours = date ? String(date.getHours()).padStart(2, "0") : "00"
  const minutes = date ? String(date.getMinutes()).padStart(2, "0") : "00"
  const seconds = date ? String(date.getSeconds()).padStart(2, "0") : "00"

  const displayValue = React.useMemo(() => {
    if (!date) return ""
    if (mode === "date") return format(date, "PPP")
    if (mode === "time") return format(date, "HH:mm:ss")
    return format(date, "PPP HH:mm:ss")
  }, [date, mode])

  const handleDaySelect = (day: Date | undefined) => {
    if (!day) return
    const current = date || new Date()
    day.setHours(current.getHours(), current.getMinutes(), current.getSeconds())
    onChange(day.toISOString())
  }

  const handleTimeChange = (
    type: "hours" | "minutes" | "seconds",
    val: string
  ) => {
    const num = parseInt(val, 10)
    if (isNaN(num)) return

    const d = date ? new Date(date) : new Date()
    if (type === "hours") d.setHours(Math.min(23, Math.max(0, num)))
    if (type === "minutes") d.setMinutes(Math.min(59, Math.max(0, num)))
    if (type === "seconds") d.setSeconds(Math.min(59, Math.max(0, num)))
    onChange(d.toISOString())
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange(null)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          className={cn(
            "w-full justify-start text-left font-normal",
            !date && "text-muted-foreground",
            hasError && "border-destructive"
          )}
        >
          {showDate && <CalendarIcon className="mr-2 h-4 w-4 shrink-0" />}
          {!showDate && showTime && (
            <Clock className="mr-2 h-4 w-4 shrink-0" />
          )}
          <span className="truncate">
            {displayValue || "Pick a date..."}
          </span>
          {date && !required && (
            <X
              className="ml-auto h-3.5 w-3.5 shrink-0 text-muted-foreground hover:text-foreground"
              onClick={handleClear}
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex flex-col">
          {showDate && (
            <Calendar
              mode="single"
              selected={date || undefined}
              onSelect={handleDaySelect}
              initialFocus
            />
          )}
          {showTime && (
            <div className="border-t p-3">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4 text-muted-foreground mr-1" />
                <TimeInput
                  value={hours}
                  onChange={(v) => handleTimeChange("hours", v)}
                  max={23}
                  label="Hours"
                />
                <span className="text-sm font-medium">:</span>
                <TimeInput
                  value={minutes}
                  onChange={(v) => handleTimeChange("minutes", v)}
                  max={59}
                  label="Minutes"
                />
                <span className="text-sm font-medium">:</span>
                <TimeInput
                  value={seconds}
                  onChange={(v) => handleTimeChange("seconds", v)}
                  max={59}
                  label="Seconds"
                />
              </div>
            </div>
          )}
          <div className="border-t p-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                onChange(new Date().toISOString())
              }}
            >
              Now
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => setOpen(false)}
            >
              Done
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

function TimeInput({
  value,
  onChange,
  max,
  label,
}: {
  value: string
  onChange: (value: string) => void
  max: number
  label: string
}) {
  return (
    <Input
      type="number"
      min={0}
      max={max}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-14 h-8 text-center text-sm px-1 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
      aria-label={label}
    />
  )
}
